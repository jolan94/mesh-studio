"""Structured C3D8 blocks. No tetra-to-hex conversion or silent fallback."""
import math
import gmsh
import numpy as np

# CalculiX local face order is inward for positive element orientation.
FACES=((0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0))

def topology(report):
    if not report['supported'] or len(report['faces'])!=6 or any(f['type']!='Plane' for f in report['faces']):
        raise ValueError('Brick meshing needs a single block with six planar four-sided faces. Partition complex geometry externally or choose C3D10 tetrahedra.')
    sides={};endpoints={};parent={}
    for face in report['faces']:
        curves=[abs(t) for d,t in gmsh.model.getBoundary([(2,face['tag'])],oriented=False) if d==1]
        if len(curves)!=4 or len(set(curves))!=4:raise ValueError('Each brick CAD face needs exactly four straight edges.')
        sides[face['tag']]=curves
        for c in curves:
            if gmsh.model.getType(1,c)!='Line':raise ValueError('Brick meshing currently requires straight CAD edges.')
            ends=set(t for d,t in gmsh.model.getBoundary([(1,c)],oriented=False) if d==0)
            if len(ends)!=2:raise ValueError('A brick edge does not have two endpoints.')
            endpoints[c]=ends;parent[c]=c
    if len(endpoints)!=12 or len(set.union(*endpoints.values()))!=8:raise ValueError('Brick meshing needs a single eight-corner block.')
    def root(c):
        while parent[c]!=c:c=parent[c]
        return c
    for curves in sides.values():
        for c in curves:
            opposite=[e for e in curves if not endpoints[c]&endpoints[e]]
            if len(opposite)!=1:raise ValueError('CAD face is not a four-corner loop.')
            parent[root(c)]=root(opposite[0])
    groups={}
    for c in endpoints:groups.setdefault(root(c),[]).append(c)
    if len(groups)!=3 or any(len(g)!=4 for g in groups.values()):raise ValueError('CAD block edge directions are inconsistent.')
    return sides,list(groups.values())

def configure(report,recipe,max_elements,max_nodes):
    sides,groups=topology(report)
    if recipe.get('local'):raise ValueError('C3D8 uses a structured global grid. Clear local refinements explicitly or use C3D10.')
    size=recipe['globalSize'];counts=[max(1,math.ceil(max(gmsh.model.occ.getMass(1,c) for c in group)/size)) for group in groups]
    if math.prod(counts)>max_elements or math.prod(n+1 for n in counts)>max_nodes:raise ValueError('Structured brick grid exceeds the element/node budget. Increase global size.')
    for group,n in zip(groups,counts):
        for c in group:gmsh.model.mesh.setTransfiniteCurve(c,n+1)
    for s in sides:gmsh.model.mesh.setTransfiniteSurface(s);gmsh.model.mesh.setRecombine(2,s)
    for _,v in gmsh.model.getEntities(3):gmsh.model.mesh.setTransfiniteVolume(v)
    gmsh.option.setNumber('Mesh.ElementOrder',1)
    return counts

def quad_shape(r,s):
    signs=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
    a=signs[:,0];b=signs[:,1]
    return (1+a*r)*(1+b*s)/4,a*(1+b*s)/4,b*(1+a*r)/4
