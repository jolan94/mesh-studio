"""Real original STEP fixtures -> quadratic mesh -> independently parsed INP -> CCX.
Analytic tests use explicit tolerances (not a claim of arbitrary model accuracy).
"""
from pathlib import Path
import sys, tempfile, subprocess, json, os, unittest
import numpy as np
from kernel import *
from solver import report_solver
ROOT=Path(__file__).resolve().parents[2]
CCX=ROOT/'runtime/bin/ccx_2.23'
OUTPUT=ROOT/'docs/verification/kernel-results.json'
RESULTS=[]

def model(name,size=4,local=None):
    initialize()
    try:
        r=import_geometry(ROOT/'fixtures'/f'{name}.step')
        m=mesh_geometry(r,{'globalSize':size,'local':local or []})
        return r,m
    finally:gmsh.finalize()

def solve(name,mesh,setup):
    folder=ROOT/'pilot-projects/benchmarks'/name;folder.mkdir(parents=True,exist_ok=True)
    export=export_deck(mesh,setup,folder/'model.inp')
    r=subprocess.run([str(CCX),'model'],cwd=folder,text=True,capture_output=True,timeout=90,env={**os.environ,'OMP_NUM_THREADS':'1','NUMBER_OF_CPUS':'1','CCX_NPROC_RESULTS':'1','CCX_NPROC_STIFFNESS':'1','CCX_NPROC_EQUATION_SOLVER':'1'})
    (folder/'solver.log').write_text(r.stdout+r.stderr)
    if r.returncode:raise RuntimeError(r.stdout[-2000:]+r.stderr)
    result,data=report_solver(folder,mesh,setup,export,r.stdout)
    RESULTS.append({'name':name,'mesh':mesh['report'],'export':export,'solver':result})
    return result,data

def setup(force=None,pressure=None):
    return {'material':{'E':210000.,'nu':.3},'supports':[{'id':'fixed','faceId':'f1','dofs':[1,2,3],'values':[0.,0.,0.]}],'loads':[{'id':'applied','faceId':'f2',**({'type':'force','vector':force} if force is not None else {'type':'pressure','value':pressure})}]}

class NumericalTests(unittest.TestCase):
    def test_axial_bar_and_refinement(self):
        r,m=model('axial-bar',4)
        for i,local in enumerate([[],[{'faceId':'f2','size':2,'distance':8}],[{'faceId':'f2','size':1.5,'distance':8}]]):
            if i:r,m=model('axial-bar',4,local)
            result,data=solve('axial-'+str(i),m,setup(force=[1000.,0,0]))
            values=[data['displacements'][n][0] for n in m['surfaces']['f2']['nodes']]
            expected=1000*40/(210000*100)
            actual=float(np.mean(values));err=abs(actual/expected-1)
            self.assertLess(err,.04) # fully fixed end suppresses Poisson contraction locally
            RESULTS[-1]['analytic']={'expectedMm':expected,'measuredMeanMm':actual,'relativeError':err,'tolerance':.04}
            np.testing.assert_allclose(result['reactionN'],[-1000,0,0],rtol=1e-4,atol=.02)
        self.assertEqual(len(r['faces']),6)

    def test_cantilever(self):
        r,m=model('cantilever',3)
        result,data=solve('cantilever',m,setup(force=[0.,0.,-100.]))
        expected=100*100**3/(3*210000*(10*10**3/12))
        measured=-float(np.mean([data['displacements'][n][2] for n in m['surfaces']['f2']['nodes']]))
        err=abs(measured/expected-1);self.assertLess(err,.04)
        RESULTS[-1]['analytic']={'reference':'Euler-Bernoulli cantilever, uniform end traction; small shear correction expected','expectedMm':expected,'measuredMeanMm':measured,'relativeError':err,'tolerance':.04}

    def test_pressure_and_all_six_boundary_directions(self):
        r,m=model('pressure-block',4)
        result,data=solve('pressure-x',m,setup(pressure=10.))
        np.testing.assert_allclose(result['reactionN'],[1000,0,0],rtol=1e-4,atol=.02)
        for face in r['faces']:
            axis=int(np.argmax(np.abs(np.array(face['center'])-np.array([10,5,5]))))
            # Fully fix the opposite plane, apply inward pressure on each boundary.
            opposite=next(f for f in r['faces'] if np.linalg.norm(np.array(f['center'])+np.array(face['center'])-np.array([20,10,10]))<1e-6)
            s={'material':{'E':210000.,'nu':.3},'supports':[{'id':'fixed','faceId':opposite['id'],'dofs':[1,2,3],'values':[0.,0.,0.]}],'loads':[{'id':'pressure','faceId':face['id'],'type':'pressure','value':2.}]}
            result,_=solve('pressure-'+face['id'],m,s)
            applied=RESULTS[-1]['export']['totalForceN']
            np.testing.assert_allclose(np.array(applied)+result['reactionN'],[0,0,0],atol=.02)

    def test_curved_hole_local_refinement(self):
        r,m=model('holed-plate',4)
        curved=next(f for f in r['faces'] if f['type']=='Cylinder')
        r,m2=model('holed-plate',4,[{'faceId':curved['id'],'size':1,'distance':4}])
        self.assertGreater(m2['report']['elementCount'],m['report']['elementCount'])
        integration=integrate_region(m2,curved['id']);expected=2*np.pi*3*6
        self.assertLess(abs(integration['area']/expected-1),.005)
        write_json('/tmp/mesh-curved.json',m2)
        report=export_deck(m2,{'material':{'E':210000.,'nu':.3},'supports':[{'id':'fixed','faceId':r['faces'][0]['id'],'dofs':[1,2,3],'values':[0.,0.,0.]}],'loads':[{'id':'curved','faceId':curved['id'],'type':'force','vector':[100.,50.,-30.]}]},'/tmp/mesh-curved.inp')
        np.testing.assert_allclose(report['totalForceN'],[100,50,-30],atol=1e-8)
        RESULTS.append({'name':'curved-hole-refinement','mesh':m2['report'],'areaError':abs(integration['area']/expected-1),'export':report})

    def test_curved_pressure_with_zero_net_force(self):
        r,m=model('holed-plate',3)
        bore=next(f for f in r['faces'] if f['type']=='Cylinder')
        bottom=next(f for f in r['faces'] if f['type']=='Plane' and abs(f['center'][2])<1e-6)
        s={'material':{'E':210000.,'nu':.3},'supports':[{'id':'bottom','faceId':bottom['id'],'dofs':[1,2,3],'values':[0.,0.,0.]}],'loads':[{'id':'bore','faceId':bore['id'],'type':'pressure','value':10.}]}
        result,data=solve('curved-pressure',m,s)
        self.assertGreater(result['maximumDisplacementMm'],0)
        self.assertLess(np.linalg.norm(RESULTS[-1]['export']['totalForceN']),.01)
        self.assertGreater(RESULTS[-1]['export']['appliedMagnitudeN'],1000)

    def test_step_units_and_unsupported_topology(self):
        with tempfile.TemporaryDirectory() as folder:
            original=(ROOT/'fixtures/axial-bar.step').read_text()
            self.assertIn('SI_UNIT(.MILLI.,.METRE.)',original)
            source=Path(folder)/'meter-bar.step';source.write_text(original.replace('SI_UNIT(.MILLI.,.METRE.)','SI_UNIT($,.METRE.)'))
            initialize()
            try:
                report=import_geometry(source)
                self.assertAlmostEqual(report['bounds'][3]-report['bounds'][0],40000,places=3)
                self.assertAlmostEqual(report['volume']/4000,1e9,places=2)
                self.assertEqual(report['sourceUnit'],'$')
            finally:gmsh.finalize()
            initialize()
            try:
                gmsh.model.occ.addBox(0,0,0,10,10,10);gmsh.model.occ.addBox(20,0,0,10,10,10);gmsh.model.occ.synchronize();gmsh.write(str(Path(folder)/'assembly.step'))
                gmsh.clear();report=import_geometry(Path(folder)/'assembly.step')
                self.assertFalse(report['supported']);self.assertEqual(report['solidCount'],2)
                with self.assertRaises(ValueError):mesh_geometry(report,{'globalSize':4})
            finally:gmsh.finalize()
            initialize()
            try:
                gmsh.model.occ.addRectangle(0,0,0,10,10);gmsh.model.occ.synchronize();gmsh.write(str(Path(folder)/'surface.step'))
                gmsh.clear();report=import_geometry(Path(folder)/'surface.step');self.assertFalse(report['supported']);self.assertEqual(report['solidCount'],0)
            finally:gmsh.finalize()

    def test_hxt_algorithm(self):
        initialize()
        try:
            report=import_geometry(ROOT/'fixtures/axial-bar.step')
            mesh=mesh_geometry(report,{'globalSize':4,'algorithm':'hxt'})
            self.assertGreater(mesh['report']['minDetJac'],0)
            result,_=solve('hxt-axial',mesh,setup(force=[1000.,0,0]))
            np.testing.assert_allclose(result['reactionN'],[-1000,0,0],atol=.02)
        finally:gmsh.finalize()

    def test_bricks_force_refinement_and_writer_order(self):
        for size in (4,2):
            initialize()
            try:
                r=import_geometry(ROOT/'fixtures/axial-bar.step');self.assertTrue(r['brickSupported'])
                m=mesh_geometry(r,{'globalSize':size,'elementType':'C3D8'})
                self.assertEqual(m['elementType'],'C3D8');self.assertTrue(all(len(e)==9 for e in m['elements']))
                with tempfile.TemporaryDirectory() as t:
                    gmsh.option.setNumber('Mesh.SaveAll',1);gmsh.write(str(Path(t)/'gmsh.inp'))
                    from deck_check import parse_deck
                    rows=[row for b in parse_deck(Path(t)/'gmsh.inp') if b['keyword']=='*ELEMENT' and b['options'].get('TYPE')=='C3D8' for row in b['rows']]
                    self.assertEqual({int(row[0]):list(map(int,row[1:])) for row in rows},{e[0]:e[1:] for e in m['elements']})
                result,data=solve('brick-axial-'+str(size),m,setup(force=[1000.,0,0]))
                expected=1000*40/(210000*100);measured=float(np.mean([data['displacements'][n][0] for n in m['surfaces']['f2']['nodes']]))
                error=abs(measured/expected-1);self.assertLess(error,.04)
                RESULTS[-1]['analytic']={'expectedMm':expected,'measuredMeanMm':measured,'relativeError':error,'tolerance':.04}
            finally:gmsh.finalize()

    def test_brick_pressure_all_faces_and_overlapping_restraint(self):
        initialize()
        try:
            r=import_geometry(ROOT/'fixtures/pressure-block.step');m=mesh_geometry(r,{'globalSize':3,'elementType':'C3D8'})
        finally:gmsh.finalize()
        for face in r['faces']:
            opposite=next(f for f in r['faces'] if np.linalg.norm(np.array(f['center'])+np.array(face['center'])-[20,10,10])<1e-6)
            s={'material':{'E':210000.,'nu':.3},'supports':[{'id':'fixed','faceId':opposite['id'],'dofs':[1,2,3],'values':[0.,0.,0.]}],'loads':[{'id':'pressure','faceId':face['id'],'type':'pressure','value':2.}]}
            result,_=solve('brick-pressure-'+face['id'],m,s)
            integration=integrate_region(m,face['id']);self.assertAlmostEqual(integration['area'],face['area'],places=7)
            outward=(np.array(face['center'])-[10,5,5]);outward/=np.linalg.norm(outward)
            np.testing.assert_allclose(RESULTS[-1]['export']['totalForceN'],-2*face['area']*outward,atol=1e-7)
        s=setup(pressure=2.);s['supports'][0]['faceId']='f3'
        solve('brick-pressure-overlapping-support',m,s)

    def test_brick_rejection_and_independent_invalid_jacobians(self):
        initialize()
        try:
            r=import_geometry(ROOT/'fixtures/holed-plate.step');self.assertFalse(r['brickSupported'])
            with self.assertRaisesRegex(ValueError,'six planar'):mesh_geometry(r,{'globalSize':4,'elementType':'C3D8'})
        finally:gmsh.finalize()
        initialize()
        try:
            r=import_geometry(ROOT/'fixtures/axial-bar.step')
            with self.assertRaisesRegex(ValueError,'Clear local'):mesh_geometry(r,{'globalSize':4,'elementType':'C3D8','local':[{'faceId':'f2','size':2,'distance':8}]})
            m=mesh_geometry(r,{'globalSize':4,'elementType':'C3D8'})
            import copy
            invalid=copy.deepcopy(m);invalid['elements'][0][1],invalid['elements'][0][2]=invalid['elements'][0][2],invalid['elements'][0][1]
            with tempfile.TemporaryDirectory() as t:
                with self.assertRaisesRegex(ValueError,'Jacobian'):export_deck(invalid,{},Path(t)/'invalid.inp','mesh')
        finally:gmsh.finalize()

    def test_incomplete_and_conflicting_setup(self):
        _,m=model('axial-bar',5)
        with tempfile.TemporaryDirectory() as t:
            self.assertTrue(export_deck(m,{},Path(t)/'mesh.inp','mesh')['passed'])
            with self.assertRaises(ValueError):export_deck(m,{},Path(t)/'bad.inp')
            s=setup(force=[1000.,0,0]);s['supports'].append({'id':'conflict','faceId':'f1','dofs':[1],'values':[1.]})
            with self.assertRaises(ValueError):export_deck(m,s,Path(t)/'conflict.inp')
            s=setup(force=[1000.,0,0]);s['supports'][0]['dofs']=[1];s['supports'][0]['values']=[0.]
            with self.assertRaises(ValueError):export_deck(m,s,Path(t)/'underconstrained.inp')

if __name__=='__main__':
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=unittest.main(verbosity=2,exit=False)
    finally:write_json(OUTPUT,{'gmsh':gmsh.__version__,'numpy':np.__version__,'solver':str(CCX),'results':RESULTS})
    sys.exit(0 if result.result.wasSuccessful() else 1)
