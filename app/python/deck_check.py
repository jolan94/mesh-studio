"""Independent parser for the intentionally small exported CalculiX dialect."""
from pathlib import Path
import math
import numpy as np

def parse_deck(path):
    blocks=[];current=None
    for line in Path(path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith('**'):continue
        if line.startswith('*'):
            parts=[x.strip().upper() for x in line.split(',')]
            current={'keyword':parts[0],'options':dict(p.split('=',1) for p in parts[1:] if '=' in p),'rows':[]};blocks.append(current)
        else:
            if current is None:raise ValueError('Data before the first INP keyword.')
            current['rows'].append([x.strip() for x in line.split(',') if x.strip()])
    return blocks

def check_deck(path,mode):
    blocks=parse_deck(path);nodes={};elements={};sets={};boundaries=[];loads=[];surfaces=[];material=False;section=False;element_type=None;pressures=[]
    for b in blocks:
        k=b['keyword'];o=b['options'];rows=b['rows']
        if k=='*NODE':
            for row in rows:
                if len(row)!=4 or int(row[0]) in nodes:raise ValueError('Invalid or duplicate node record.')
                xyz=list(map(float,row[1:]));
                if not all(math.isfinite(x) for x in xyz):raise ValueError('Non-finite node coordinate.')
                nodes[int(row[0])]=np.array(xyz)
        elif k=='*ELEMENT':
            kind=o.get('TYPE')
            if kind not in ('C3D10','C3D8') or element_type not in (None,kind):raise ValueError('Unsupported or mixed element families.')
            element_type=kind;width=10 if kind=='C3D10' else 8
            for row in rows:
                vals=list(map(int,row))
                if len(vals)!=width+1 or vals[0] in elements or len(set(vals[1:]))!=width:raise ValueError('Invalid volume element connectivity.')
                elements[vals[0]]=vals[1:]
        elif k=='*NSET':sets[o['NSET']]=[int(x) for row in rows for x in row]
        elif k=='*SURFACE':surfaces+=rows
        elif k=='*BOUNDARY':boundaries+=rows
        elif k=='*CLOAD':loads+=rows
        elif k=='*DLOAD':
            for row in rows:
                pressures.append(row)
        elif k=='*ELASTIC':
            E,nu=map(float,rows[0]);material=math.isfinite(E) and E>0 and -.99<=nu<.5
        elif k=='*SOLID SECTION':section=o.get('ELSET')=='SOLID' and o.get('MATERIAL')=='ELASTIC'
    if not nodes or not elements:raise ValueError('Deck has no volume mesh.')
    adjacency={};edges={}
    localfaces=((0,1,2),(0,3,1),(1,3,2),(2,3,0));localedges=((0,1),(1,2),(2,0),(0,3),(1,3),(2,3))
    if element_type=='C3D8':
        localfaces=((0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0))
        signs=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],dtype=float)
        locations=sorted(set([-1.,0.,1.,-1/np.sqrt(3),1/np.sqrt(3)]))
        derivatives=[];a,b,c=signs.T
        for r in locations:
            for t in locations:
                for u in locations:derivatives.append(np.array([a*(1+b*t)*(1+c*u),b*(1+a*r)*(1+c*u),c*(1+a*r)*(1+b*t)]).T/8)
        derivatives=np.array(derivatives)
    for eid,conn in elements.items():
        if any(n not in nodes for n in conn):raise ValueError('Element references an absent node.')
        if element_type=='C3D10':
            a,b,c,d=(nodes[n] for n in conn[:4])
            if np.linalg.det(np.array([b-a,c-a,d-a]))<=0:raise ValueError('Tetrahedral corner orientation is non-positive.')
        else:
            xyz=np.array([nodes[n] for n in conn])
            det=np.linalg.det(np.einsum('ni,pnj->pij',xyz,derivatives))
            if not np.all(np.isfinite(det)) or np.min(det)<=0:raise ValueError('Brick has a non-positive sampled Jacobian.')
        for f in localfaces:
            key=tuple(sorted(conn[i] for i in f));adjacency[key]=adjacency.get(key,0)+1
        for mid,(i,j) in zip(conn[4:] if element_type=='C3D10' else [],localedges):
            edge=tuple(sorted((conn[i],conn[j])))
            if edge in edges and edges[edge]!=mid:raise ValueError('Quadratic edge nodes are not shared consistently.')
            edges[edge]=mid
    for eid,side in surfaces:
        eid=int(eid)
        if eid not in elements or side not in tuple('S'+str(i) for i in range(1,len(localfaces)+1)):raise ValueError('Surface references an absent element or invalid face.')
        conn=elements[eid];key=tuple(sorted(conn[i] for i in localfaces[int(side[1])-1]))
        if adjacency[key]!=1:raise ValueError('Exported surface is not an exterior volume face.')
    for row in pressures:
        eid=int(row[0]);side=row[1]
        if eid not in elements or side not in tuple('P'+str(i) for i in range(1,len(localfaces)+1)) or not math.isfinite(float(row[2])):raise ValueError('Invalid pressure-face record.')
        key=tuple(sorted(elements[eid][i] for i in localfaces[int(side[1])-1]))
        if adjacency[key]!=1:raise ValueError('Pressure is not on an exterior volume face.')
    for ids in sets.values():
        if len(ids)!=len(set(ids)) or any(n not in nodes for n in ids):raise ValueError('Node set is invalid.')
    restraint=[]
    for row in boundaries:
        if row[0] not in sets:raise ValueError('Support node set is missing.')
        low,high=int(row[1]),int(row[2]);value=float(row[3])
        if low<1 or high>3 or low>high or not math.isfinite(value):raise ValueError('Unsupported boundary definition.')
        for n in sets[row[0]]:
            x,y,z=nodes[n]
            rigid=np.array([[1,0,0,0,z,-y],[0,1,0,-z,0,x],[0,0,1,y,-x,0]],dtype=float)
            restraint.extend(rigid[low-1:high])
    for row in loads:
        if int(row[0]) not in nodes or int(row[1]) not in (1,2,3) or not math.isfinite(float(row[2])):raise ValueError('Invalid nodal force.')
    rank=int(np.linalg.matrix_rank(np.array(restraint))) if restraint else 0
    if mode=='analysis':
        if not material or not section:raise ValueError('Material or solid section is missing.')
        if rank<6:raise ValueError(f'Supports restrain only {rank} of 6 rigid-body modes. Add sufficient restraints.')
        if not any(b['keyword']=='*STEP' for b in blocks) or blocks[-1]['keyword']!='*END STEP':raise ValueError('Analysis step is incomplete.')
    return {'passed':True,'nodeCount':len(nodes),'elementCount':len(elements),'exteriorSurfaceFaces':len(surfaces),'rigidBodyRestraintRank':rank,'elementType':element_type,'checks':['References','C3D10 corner orientation' if element_type=='C3D10' else 'C3D8 sampled Jacobians','Shared quadratic edges' if element_type=='C3D10' else 'Brick face adjacency','Exterior pressure faces','Finite values','Rigid-body restraint' if mode=='analysis' else 'Mesh-only deck']}
