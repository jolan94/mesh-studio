from pathlib import Path
import re,numpy as np

def parse_dat(path):
    text=Path(path).read_text();data={};kind=None
    for line in text.splitlines():
        if 'displacements (vx,vy,vz)' in line:kind='displacements';data[kind]={};continue
        if 'forces (fx,fy,fz)' in line:kind='forces';data[kind]={};continue
        vals=line.split()
        if kind and len(vals)==4 and vals[0].isdigit():
            try:data[kind][int(vals[0])]=[float(x.replace('D','E')) for x in vals[1:]]
            except ValueError:pass
        elif line.strip() and not (len(vals)==4 and vals[0].isdigit()):kind=None
    if not data.get('displacements') or not data.get('forces'):raise ValueError('CalculiX did not produce displacement and force records.')
    return data

def report_solver(folder,mesh,setup,export,log):
    if '*ERROR' in log.upper() or 'JOB FINISHED' not in log.upper():raise ValueError('CalculiX did not finish cleanly. Inspect the saved solver log.')
    data=parse_dat(Path(folder)/'model.dat')
    reactions=np.zeros(3);seen=set()
    for support in setup['supports']:
        for n in mesh['surfaces'][support['faceId']]['nodes']:
            for d in support.get('dofs',[1,2,3]):
                if (n,d) not in seen:
                    reactions[d-1]+=data['forces'][n][d-1];seen.add((n,d))
    reactions-=np.array(export.get('loadingOnRestrainedN',[0,0,0]))
    applied=np.array(export['totalForceN']);residual=reactions+applied
    tolerance=max(1e-5,export.get('appliedMagnitudeN',np.linalg.norm(applied))*2e-4)
    if np.linalg.norm(residual)>tolerance:raise ValueError('Solver reaction balance did not pass.')
    coords={n[0]:np.array(n[1:]) for n in mesh['nodes']};reaction_moment=np.zeros(3)
    for n in set(n for n,d in seen):
        r=np.zeros(3)
        for d in range(1,4):
            if (n,d) in seen:r[d-1]=data['forces'][n][d-1]
        reaction_moment+=np.cross(coords[n],r)
    reaction_moment-=np.array(export.get('loadingOnRestrainedMomentNmm',[0,0,0]))
    moment_residual=reaction_moment+np.array(export['totalMomentNmm'])
    span=max(np.linalg.norm(x) for x in coords.values())
    if np.linalg.norm(moment_residual)>max(1e-4,tolerance*span*2):raise ValueError('Solver reaction moment did not pass.')
    return {'passed':True,'solverVersion':'CalculiX 2.23 (static SPOOLES build)','deckHash':export['sha256'],'reactionN':reactions.tolist(),'balanceResidualN':residual.tolist(),'momentResidualNmm':moment_residual.tolist(),'maximumDisplacementMm':max(np.linalg.norm(v) for v in data['displacements'].values()),'note':'Linear static execution and balance checked. Solution convergence has not been established.'},data
