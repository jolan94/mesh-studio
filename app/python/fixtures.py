from pathlib import Path
import gmsh

def create(folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    gmsh.initialize(readConfigFiles=False)
    gmsh.option.setNumber('General.Terminal', 0)
    for name, dims in [('axial-bar',(40,10,10)),('cantilever',(100,10,10)),('pressure-block',(20,10,10)),('block',(20,20,20))]:
        gmsh.clear(); gmsh.model.add(name)
        gmsh.model.occ.addBox(0,0,0,*dims); gmsh.model.occ.synchronize()
        gmsh.write(str(folder / (name+'.step')))
    gmsh.clear(); gmsh.model.add('holed-plate')
    box=gmsh.model.occ.addBox(0,0,0,40,20,6)
    cyl=gmsh.model.occ.addCylinder(20,10,0,0,0,6,3)
    gmsh.model.occ.cut([(3,box)],[(3,cyl)]); gmsh.model.occ.synchronize()
    gmsh.write(str(folder/'holed-plate.step'))
    gmsh.finalize()
if __name__=='__main__':
    import sys
    create(sys.argv[1])
