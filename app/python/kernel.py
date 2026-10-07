"""Authoritative STEP/OCCT import, quadratic tetra meshing and CalculiX setup.
No user-supplied code. All lengths normalized by OCCT to mm; forces N, E MPa.
"""
from pathlib import Path
from collections import defaultdict
import hashlib, json, math, re
import gmsh
import numpy as np

MAX_ELEMENTS=150000
MAX_NODES=350000
FACES=((0,1,2,4,5,6),(0,3,1,7,8,4),(1,3,2,8,9,5),(2,3,0,9,7,6))

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value): Path(path).write_text(json.dumps(value,allow_nan=False))
def stage(text): print(json.dumps({'event':'stage','stage':text}),flush=True)
def finite(value,label,minimum=None,maximum=None):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError(label+' must be a finite number.')
    if minimum is not None and value<minimum or maximum is not None and value>maximum: raise ValueError(label+' is outside the supported range.')
    return float(value)

def ccx_number(value):
    # CalculiX input numeric fields are at most 20 characters.
    for precision in range(17,9,-1):
        text=format(float(value),f'.{precision}g')
        if len(text)<=20:return text
    raise ValueError('Number exceeds the CalculiX numeric-field budget.')

def initialize():
    if gmsh.__version__!='4.15.2':raise ValueError('Select a Python runtime with Gmsh 4.15.2. See Setup.')
    gmsh.initialize(readConfigFiles=False)
    gmsh.option.setNumber('General.Terminal',0)
    gmsh.option.setNumber('General.NumThreads',2)
    gmsh.option.setString('Geometry.OCCTargetUnit','MM')
    gmsh.logger.start()

def import_geometry(source):
    source=Path(source)
    if source.stat().st_size>100*1024**2: raise ValueError('STEP exceeds the 100 MB import budget.')
    text=source.read_text(errors='replace')
    if 'ISO-10303-21' not in text[:1024]: raise ValueError('Select an ISO-10303-21 STEP file.')
    si=re.findall(r'SI_UNIT\s*\(\s*(\$|\.\w+\.)\s*,\s*\.METRE\.\s*\)',text,re.I)
    conversions=[]
    for unit in re.finditer(r"CONVERSION_BASED_UNIT\s*\(\s*'([^']+)'",text,re.I):
        definition=text[text.rfind(';',0,unit.start())+1:text.find(';',unit.end())]
        if 'LENGTH_UNIT' in definition.upper():conversions.append(unit.group(1))
    source_unit='; '.join(sorted(set(si+conversions))) or 'unrecognized'
    gmsh.model.occ.importShapes(str(source),highestDimOnly=False);gmsh.model.occ.synchronize()
    solids=gmsh.model.getEntities(3); surfaces=gmsh.model.getEntities(2)
    bounds=gmsh.model.getBoundingBox(-1,-1)
    faces=[]
    for _,tag in surfaces:
        faces.append({'id':f'f{tag}','tag':tag,'name':f'Face {tag}','type':gmsh.model.getType(2,tag),'area':gmsh.model.occ.getMass(2,tag),'center':list(gmsh.model.occ.getCenterOfMass(2,tag)),'bounds':list(gmsh.model.getBoundingBox(2,tag))})
    boundary=set(abs(t) for _,t in gmsh.model.getBoundary(solids,combined=True,oriented=True)) if solids else set()
    volume=sum(gmsh.model.occ.getMass(3,t) for _,t in solids)
    issues=[]
    if len(solids)!=1: issues.append(f'Volume meshing requires one closed solid; imported {len(solids)} solids.')
    if len(surfaces)!=len(boundary): issues.append('The STEP includes surfaces outside the solid boundary.')
    if volume<=0: issues.append('No positive solid volume was imported.')
    if source_unit=='unrecognized': issues.append('The STEP length unit is unrecognized. Confirm the normalized dimensions before meshing.')
    report={'sourceHash':digest(source),'units':'mm','sourceUnit':source_unit,'bounds':list(bounds),'volume':volume,'solidCount':len(solids),'faces':faces,'issues':issues,'supported':len(solids)==1 and len(surfaces)==len(boundary) and volume>0,'backend':f'Gmsh {gmsh.__version__} / OCCT'}
    from bricks import topology
    try:topology(report);report['brickSupported']=True
    except ValueError:report['brickSupported']=False
    return report

def check_identity(report,expected):
    if not expected: return
    if report['sourceHash']!=expected['sourceHash']: raise ValueError('Source STEP changed since inspection.')
    old={f['id']:f for f in expected['faces']}
    if len(old)!=len(report['faces']): raise ValueError('Imported topology changed; inspect and select regions again.')
    for f in report['faces']:
        o=old.get(f['id'])
        if not o or o['type']!=f['type'] or not np.allclose(o['center'],f['center'],rtol=1e-9,atol=1e-7) or not math.isclose(o['area'],f['area'],rel_tol=1e-9,abs_tol=1e-7): raise ValueError('Region identity changed; inspect and select regions again.')

def sizing(report,recipe):
    size=finite(recipe.get('globalSize',3),'Global size',.02,10000)
    if report['volume']/size**3*10>MAX_ELEMENTS: raise ValueError('Requested global size exceeds the element budget. Increase it.')
    gmsh.option.setNumber('Mesh.Algorithm3D',{'delaunay':1,'hxt':10}.get(recipe.get('algorithm','delaunay'),1))
    if recipe.get('algorithm','delaunay') not in ('delaunay','hxt'): raise ValueError('Choose Delaunay or HXT.')
    gmsh.option.setNumber('Mesh.MeshSizeMin',size)
    gmsh.option.setNumber('Mesh.MeshSizeMax',size)
    gmsh.option.setNumber('Mesh.MeshSizeFromPoints',0);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',0);gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',0)
    local=recipe.get('local',[])
    if len(local)>12: raise ValueError('At most 12 refinement regions are supported.')
    fields=[];minimum=size
    for region in local:
        match=[f for f in report['faces'] if f['id']==region['faceId']]
        if not match: raise ValueError('Refinement face is missing.')
        target=finite(region['size'],'Local size',.02,size)
        distance=finite(region.get('distance',size*2),'Transition distance',target,10000)
        minimum=min(minimum,target)
        field=gmsh.model.mesh.field.add('Distance');gmsh.model.mesh.field.setNumbers(field,'FacesList',[match[0]['tag']]);gmsh.model.mesh.field.setNumber(field,'Sampling',100)
        threshold=gmsh.model.mesh.field.add('Threshold')
        for key,value in {'InField':field,'SizeMin':target,'SizeMax':size,'DistMin':0,'DistMax':distance}.items():gmsh.model.mesh.field.setNumber(threshold,key,value)
        fields.append(threshold)
    if fields:
        minimum_field=gmsh.model.mesh.field.add('Min');gmsh.model.mesh.field.setNumbers(minimum_field,'FieldsList',fields);gmsh.model.mesh.field.setAsBackgroundMesh(minimum_field)
        gmsh.option.setNumber('Mesh.MeshSizeMin',minimum)
    return size

def extract_surfaces(report,mesh=None):
    surfaces={}
    adjacency={}
    face_indices=__import__('bricks').FACES if mesh and mesh.get('elementType')=='C3D8' else FACES
    corners=4 if mesh and mesh.get('elementType')=='C3D8' else 3
    if mesh:
        for eid,*conn in mesh['elements']:
            for side,indices in enumerate(face_indices,1):
                key=tuple(sorted(conn[i] for i in indices[:corners]))
                adjacency.setdefault(key,[]).append((eid,side))
    for face in report['faces']:
        types,tags,connectivity=gmsh.model.mesh.getElements(2,face['tag'])
        tris=[];mapped=[]
        for kind,ids,nodes in zip(types,tags,connectivity):
            if kind not in (2,9,3): raise ValueError('Unsupported boundary face element.')
            if mesh and (kind==3)!=(mesh.get('elementType')=='C3D8'):raise ValueError('Boundary family disagrees with the volume family.')
            width={2:3,9:6,3:4}[kind]
            for tri in nodes.reshape(-1,width).tolist():
                tris.append(tri)
                if mesh:
                    matches=adjacency.get(tuple(sorted(tri[:corners])),[])
                    if len(matches)!=1: raise ValueError('Boundary face has no unique adjacent volume element.')
                    eid,side=matches[0]
                    conn=next_element_map(mesh)[eid]
                    if set(tri)!=set(conn[i] for i in face_indices[side-1]): raise ValueError('Quadratic surface nodes disagree with the volume face.')
                    mapped.append([eid,side])
        surfaces[face['id']]={'triangles':tris,'elementFaces':mapped,'nodes':sorted(set(n for tri in tris for n in tri))}
    return surfaces

def next_element_map(mesh):
    # Build once per extraction, but never serialize the transient lookup.
    if '_elements' not in mesh:mesh['_elements']={e[0]:e[1:] for e in mesh['elements']}
    return mesh['_elements']

def mesh_geometry(report,recipe):
    element_type=recipe.get('elementType','C3D10')
    if element_type not in ('C3D10','C3D8'):raise ValueError('Choose C3D10 tetrahedra or C3D8 bricks.')
    if not report['supported']: raise ValueError('; '.join(report['issues']))
    if report['sourceUnit']=='unrecognized' and not recipe.get('unitsConfirmed'): raise ValueError('Confirm normalized millimeter dimensions before meshing.')
    if element_type=='C3D8':
        finite(recipe.get('globalSize'),'Global size',.02,10000)
        from bricks import configure
        configure(report,recipe,MAX_ELEMENTS,MAX_NODES);stage('Generating structured bricks')
    else:sizing(report,recipe);stage('Generating tetrahedra')
    gmsh.model.mesh.generate(3)
    if sum(len(t) for t in gmsh.model.mesh.getElements(3)[1])>MAX_ELEMENTS: raise ValueError('Mesh exceeds the element budget; previous mesh is preserved.')
    if element_type=='C3D10':
        gmsh.model.mesh.optimize('Netgen');stage('Creating quadratic elements')
        gmsh.model.mesh.setOrder(2);gmsh.model.mesh.optimize('HighOrder')
    types,tags,connections=gmsh.model.mesh.getElements(3)
    elements=[];alltags=[]
    for kind,ids,nodes in zip(types,tags,connections):
        expected_kind,width=(5,8) if element_type=='C3D8' else (11,10)
        if kind!=expected_kind:raise ValueError('Mesher returned a different element family; no mixed mesh or fallback is exported.')
        for eid,conn in zip(ids.tolist(),nodes.reshape(-1,width).tolist()):
            # Gmsh INP writer's C3D10 conversion, verified against its output.
            if element_type=='C3D10':conn[8],conn[9]=conn[9],conn[8]
            elements.append([eid,*conn]);alltags.append(eid)
    nodeids,xyz,_=gmsh.model.mesh.getNodes();xyz=xyz.reshape(-1,3)
    if len(nodeids)>MAX_NODES: raise ValueError('Mesh exceeds the node budget.')
    stage('Checking curved Jacobians and boundary mappings')
    det=np.array(gmsh.model.mesh.getElementQualities(alltags,'minDetJac'))
    sicn=np.array(gmsh.model.mesh.getElementQualities(alltags,'minSICN'))
    sj=np.array(gmsh.model.mesh.getElementQualities(alltags,'minSJ'))
    if not len(elements) or not np.all(np.isfinite(det)) or min(det)<=0: raise ValueError('Mesh has non-positive curved-element Jacobians.')
    mesh={'nodes':[[int(i),*p.tolist()] for i,p in zip(nodeids,xyz)],'elements':elements,'elementType':element_type,'report':{'elementType':element_type,'passed':True,'nodeCount':len(nodeids),'elementCount':len(elements),'minDetJac':float(min(det)),'minSICN':float(min(sicn)),'p05SICN':float(np.percentile(sicn,5)),'minSJ':float(min(sj)),'warnings':(['Low shape quality: inspect the highlighted minimum-quality elements.'] if min(sicn)<.1 else [])+(['Structured C3D8: global grid only. Full-integration bricks can be too stiff in bending; verify mesh convergence.'] if element_type=='C3D8' else []),'worstElements':[int(alltags[i]) for i in np.argsort(sicn)[:10]],'geometryHash':report['sourceHash'],'solver':'Not run'}}
    mesh['surfaces']=extract_surfaces(report,mesh);mesh.pop('_elements',None)
    # Boundary conformity: midside nodes must remain on the imported CAD surfaces.
    residual=0
    coords={n[0]:n[1:] for n in mesh['nodes']}
    for face in report['faces']:
        ids=mesh['surfaces'][face['id']]['nodes'];points=[x for i in ids for x in coords[i]]
        closest,_=gmsh.model.getClosestPoint(2,face['tag'],points)
        residual=max(residual,float(np.max(np.linalg.norm(np.array(points).reshape(-1,3)-np.array(closest).reshape(-1,3),axis=1))))
    mesh['report']['maxBoundaryDistanceMm']=residual
    if residual>max(1e-6,recipe['globalSize']*1e-5): raise ValueError('Mesh boundary deviates from the imported CAD surface.')
    return mesh

def preview(report):
    if not report['faces']:return {'nodes':[],'surfaces':{}}
    span=max(report['bounds'][i+3]-report['bounds'][i] for i in range(3))
    gmsh.option.setNumber('Mesh.MeshSizeMax',max(span/12,.1));gmsh.option.setNumber('Mesh.MeshSizeMin',max(span/20,.05))
    gmsh.model.mesh.generate(2)
    ids,xyz,_=gmsh.model.mesh.getNodes()
    return {'nodes':[[int(i),*p.tolist()] for i,p in zip(ids,xyz.reshape(-1,3))],'surfaces':extract_surfaces(report)}

# Tensor quadrature on a Duffy triangle, handles curved six-node surfaces.
_G,_W=np.polynomial.legendre.leggauss(8);_G=(_G+1)/2;_W=_W/2
QUAD=[(u,(1-u)*v,wu*wv*(1-u)) for u,wu in zip(_G,_W) for v,wv in zip(_G,_W)]
def shape(r,s):
    a=1-r-s
    N=np.array([a*(2*a-1),r*(2*r-1),s*(2*s-1),4*a*r,4*r*s,4*s*a])
    dr=np.array([1-4*a,4*r-1,0,4*(a-r),4*s,-4*s])
    ds=np.array([1-4*a,0,4*s-1,-4*r,4*r,4*(a-s)])
    return N,dr,ds

def integrate_region(mesh,faceid):
    surface=mesh['surfaces'].get(faceid)
    if not surface:raise ValueError('Selected face is missing from this mesh.')
    coords={n[0]:np.array(n[1:]) for n in mesh['nodes']};emap={e[0]:e[1:] for e in mesh['elements']}
    weights=defaultdict(float);normal_weights=defaultdict(lambda:np.zeros(3));area=0.;center=np.zeros(3);normal_integral=np.zeros(3);normal_moment=np.zeros(3)
    is_brick=mesh.get('elementType')=='C3D8'
    if is_brick:
        from bricks import FACES as brick_faces,quad_shape
        q,w=np.polynomial.legendre.leggauss(4);quadrature=[(r,s,wr*ws) for r,wr in zip(q,w) for s,ws in zip(q,w)]
    else:quadrature=QUAD
    for tri,(eid,side) in zip(surface['triangles'],surface['elementFaces']):
        tri=[emap[eid][i] for i in (brick_faces if is_brick else FACES)[side-1]]
        points=np.array([coords[n] for n in tri])
        for r,s,w in quadrature:
            N,dr,ds=quad_shape(r,s) if is_brick else shape(r,s);pos=N@points;cross=-np.cross(dr@points,ds@points) # CCX local face ordering points inward for positive tet orientation
            da=np.linalg.norm(cross)*w;area+=da;center+=pos*da;normal_integral+=cross*w;normal_moment+=np.cross(pos,cross)*w
            for n,phi in zip(tri,N):
                weights[n]+=phi*da;normal_weights[n]+=phi*cross*w
    if area<=0:raise ValueError('Selected surface has zero mesh area.')
    return {'area':area,'center':center/area,'weights':weights,'normalWeights':normal_weights,'normalIntegral':normal_integral,'normalMoment':normal_moment}

def validate_setup(setup,mesh):
    issues=[];material=setup.get('material')
    if not material:issues.append('Define elastic modulus E and Poisson ratio nu.')
    else:
        finite(material.get('E'),'Elastic modulus',.000001,1e12);finite(material.get('nu'),'Poisson ratio',-.99,.4999)
    supports=setup.get('supports',[]);loads=setup.get('loads',[])
    if not supports:issues.append('Define supports; rigid-body restraint must be reviewed.')
    if not loads:issues.append('Define at least one nonzero load.')
    ids=set();prescribed={};nonzero=False
    for item in supports+loads:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}',item.get('id','')) or item['id'] in ids:raise ValueError('Setup item IDs must be unique short names.')
        ids.add(item['id'])
        if item.get('faceId') not in mesh['surfaces']:raise ValueError('Setup references a missing CAD face.')
    for support in supports:
        dofs=support.get('dofs',[1,2,3]);values=support.get('values',[0]*len(dofs))
        if not dofs or len(dofs)!=len(set(dofs)) or any(d not in (1,2,3) for d in dofs) or len(values)!=len(dofs):raise ValueError('Support uses translation directions 1, 2, 3 with matching values.')
        for d,v in zip(dofs,values):
            finite(v,'Prescribed displacement',-1e6,1e6)
            for node in mesh['surfaces'][support['faceId']]['nodes']:
                key=(node,d)
                if key in prescribed and not math.isclose(prescribed[key],v,abs_tol=1e-12):raise ValueError('Overlapping supports prescribe conflicting displacements.')
                prescribed[key]=v
    for load in loads:
        if load.get('type')=='force':
            vector=load.get('vector',[])
            if len(vector)!=3:raise ValueError('Force needs [Fx, Fy, Fz] in N.')
            for v in vector:finite(v,'Force',-1e12,1e12)
            nonzero|=np.linalg.norm(vector)>0
        elif load.get('type')=='pressure':nonzero|=finite(load.get('value'),'Pressure MPa',-1e9,1e9)!=0
        else:raise ValueError('Supported loads are total force or normal pressure.')
    if loads and not nonzero:issues.append('All applied loads are zero.')
    return issues

def export_deck(mesh,setup,destination,mode='analysis'):
    if mode not in ('mesh','analysis'):raise ValueError('Export mesh or analysis INP.')
    issues=validate_setup(setup,mesh)
    if mode=='analysis' and issues:raise ValueError(' '.join(issues))
    element_type=mesh.get('elementType','C3D10')
    if element_type not in ('C3D10','C3D8'):raise ValueError('Unsupported export element family.')
    lines=[f'** Mesh Studio: mm, N, MPa. {element_type}.','*NODE']
    lines += [', '.join([str(n[0]),*(ccx_number(x) for x in n[1:])]) for n in mesh['nodes']]
    lines+=[f'*ELEMENT, TYPE={element_type}, ELSET=SOLID']+[', '.join(map(str,e)) for e in mesh['elements']]
    lines+=['*NSET, NSET=ALLNODES']
    allids=[n[0] for n in mesh['nodes']]
    lines += [', '.join(map(str,allids[i:i+16])) for i in range(0,len(allids),16)]
    # Named CAD surface definitions survive remeshing by rebuilding volume faces.
    for faceid,surf in mesh['surfaces'].items():
        lines+=['*NSET, NSET='+faceid.upper()]
        lines += [', '.join(map(str,surf['nodes'][i:i+16])) for i in range(0,len(surf['nodes']),16)]
        lines+=['*SURFACE, TYPE=ELEMENT, NAME=SURF_'+faceid.upper()]
        lines += [f'{eid}, S{side}' for eid,side in surf['elementFaces']]
    resultants=[];nodal=defaultdict(lambda:np.zeros(3));external=defaultdict(lambda:np.zeros(3));force=np.zeros(3);moment=np.zeros(3)
    if mode=='analysis':
        m=setup['material'];lines+=['*MATERIAL, NAME=ELASTIC','*ELASTIC',f"{ccx_number(m['E'])}, {ccx_number(m['nu'])}",'*SOLID SECTION, ELSET=SOLID, MATERIAL=ELASTIC','*STEP','*STATIC','*BOUNDARY']
        for s in setup['supports']:
            for dof,value in zip(s.get('dofs',[1,2,3]),s.get('values',[0]*len(s.get('dofs',[1,2,3])))):
                lines.append(f"{s['faceId'].upper()}, {dof}, {dof}, {ccx_number(value)}")
        for load in setup['loads']:
            integration=integrate_region(mesh,load['faceId'])
            if load['type']=='force':
                f=np.array(load['vector'],dtype=float);mom=np.cross(integration['center'],f)
                for node,w in integration['weights'].items():
                    contribution=f*w/integration['area'];nodal[node]+=contribution;external[node]+=contribution
            else:
                f=-load['value']*integration['normalIntegral'];mom=-load['value']*integration['normalMoment']
                for node,nw in integration['normalWeights'].items():external[node]-=load['value']*nw
                lines+=['*DLOAD']+[f"{eid}, P{side}, {ccx_number(load['value'])}" for eid,side in mesh['surfaces'][load['faceId']]['elementFaces']]
            force+=f;moment+=mom
            resultants.append({'id':load['id'],'areaMm2':integration['area'],'forceN':f.tolist(),'momentNmm':mom.tolist(),'magnitudeN':float(np.linalg.norm(f)) if load['type']=='force' else abs(load['value'])*integration['area']})
        if nodal:
            lines+=['*CLOAD']
            for node,f in sorted(nodal.items()):
                for dof,v in enumerate(f,1):
                    if v!=0:lines.append(f'{node}, {dof}, {ccx_number(v)}')
            coords={n[0]:np.array(n[1:]) for n in mesh['nodes']}
            expected=np.sum([np.array(l['vector']) for l in setup['loads'] if l['type']=='force'],axis=0)
            actual=sum(nodal.values(),np.zeros(3))
            if not np.allclose(actual,expected,rtol=1e-9,atol=1e-8):raise ValueError('Distributed force failed the resultant check.')
            expected_moment=sum((np.cross(integrate_region(mesh,l['faceId'])['center'],l['vector']) for l in setup['loads'] if l['type']=='force'),np.zeros(3))
            actual_moment=sum((np.cross(coords[n],f) for n,f in nodal.items()),np.zeros(3))
            if not np.allclose(actual_moment,expected_moment,rtol=1e-9,atol=1e-7):raise ValueError('Distributed force failed the moment check.')
        lines+=['*NODE PRINT, NSET=ALLNODES','U, RF','*END STEP']
    constrained=set()
    for support in setup.get('supports',[]) if mode=='analysis' else []:
        constrained.update((n,d) for n in mesh['surfaces'][support['faceId']]['nodes'] for d in support.get('dofs',[1,2,3]))
    loading_on_restraint=np.zeros(3);loading_restraint_moment=np.zeros(3);coords={n[0]:np.array(n[1:]) for n in mesh['nodes']}
    for node in set(n for n,d in constrained):
        constrained_load=np.array([external[node][d-1] if (node,d) in constrained else 0. for d in (1,2,3)])
        loading_on_restraint+=constrained_load;loading_restraint_moment+=np.cross(coords[node],constrained_load)
    Path(destination).write_text('\n'.join(lines)+'\n')
    from deck_check import check_deck
    independent=check_deck(destination,mode)
    return {'mode':mode,'passed':True,'sha256':digest(destination),'fileCheck':independent,'loads':resultants,'totalForceN':force.tolist(),'totalMomentNmm':moment.tolist(),'loadingOnRestrainedN':loading_on_restraint.tolist(),'loadingOnRestrainedMomentNmm':loading_restraint_moment.tolist(),'appliedMagnitudeN':sum(l['magnitudeN'] for l in resultants),'solver':'Not run','setupIssues':issues}
