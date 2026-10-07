from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,hashlib,tarfile
root=Path(__file__).resolve().parents[2]/'runtime';archive=root/'src/arpack.tgz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='f6641deb07fa69165b7815de9008af3ea47eb39b2bb97521fbf74c97aba6e844'
with tarfile.open(archive) as t:t.extractall(root/'src',filter='data')
source=root/'src/arpack-ng-3.9.1';build=root/'src/arpack-serial';build.mkdir(exist_ok=True)
files=list((source/'SRC').glob('*.f'))+[f for f in (source/'UTIL').glob('*.f') if f.name not in ('second_NONE.f',)]
def compile(f):
    output=build/(f.stem+'.o');subprocess.run(['/opt/homebrew/bin/gfortran-15','-O2','-fallow-argument-mismatch','-I'+str(source/'SRC'),'-c',str(f),'-o',str(output)],check=True,capture_output=True);return str(output)
with ThreadPoolExecutor(max_workers=4) as pool:objects=list(pool.map(compile,files))
subprocess.run(['/usr/bin/ar','rcs',str(root/'bin/libarpack.a'),*objects],check=True)
print('Built serial ARPACK 3.9.1',len(objects),'routines')
