import sys,json,traceback
from pathlib import Path
from kernel import *

def run(request):
    action=request['action'];out=Path(request['out']);out.mkdir(parents=True,exist_ok=True)
    if action in ('inspect','mesh'):
        initialize()
        try:
            stage('Importing STEP geometry')
            report=import_geometry(request['source']);check_identity(report,request.get('geometry'))
            write_json(out/'geometry.json',report)
            if action=='inspect':
                scene=preview(report);write_json(out/'scene.json',scene)
                return {'geometry':report,'scene':'scene.json'}
            mesh=mesh_geometry(report,request['recipe']);write_json(out/'mesh.json',mesh)
            gmsh.write(str(out/'mesh.msh'))
            return {'report':mesh['report'],'meshHash':digest(out/'mesh.json'),'mesh':'mesh.json'}
        finally:gmsh.finalize()
    if action=='solver_report':
        from solver import report_solver
        mesh=json.loads(Path(request['mesh']).read_text())
        report,_=report_solver(out,mesh,request['setup'],request['export'],(out/'solver.log').read_text())
        return report
    if action in ('export','check'):
        mesh=json.loads(Path(request['mesh']).read_text())
        return export_deck(mesh,request.get('setup',{}),out/'model.inp',request.get('mode','analysis'))
    raise ValueError('Unsupported worker operation.')

if __name__=='__main__':
    try:
        request=json.loads(Path(sys.argv[1]).read_text());result=run(request)
        print(json.dumps({'ok':True,'result':result},allow_nan=False),flush=True)
    except Exception as e:
        print(json.dumps({'ok':False,'error':str(e)}),flush=True);sys.exit(1)
