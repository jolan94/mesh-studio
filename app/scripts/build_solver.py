"""Build pinned static-analysis CalculiX locally without upgrading Homebrew."""
from pathlib import Path
import hashlib,tarfile,subprocess,os
root=Path(__file__).resolve().parents[2]/'runtime';src=root/'src'
for name,sha in [('ccx.tar.bz2','9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7'),('spooles.tgz','a84559a0e987a1e423055ef4fdf3035d55b65bbe4bf915efaa1a35bef7f8c5dd')]:
    assert hashlib.sha256((src/name).read_bytes()).hexdigest()==sha,'Archive hash mismatch'
    target=src/('spooles' if name.startswith('spooles') else 'calculix');target.mkdir(exist_ok=True)
    with tarfile.open(src/name) as t:t.extractall(target,filter='data')
sp=src/'spooles'
def replace(path,old,new):
    p=Path(path);p.write_text(p.read_text().replace(old,new))
replace(sp/'Make.inc','/usr/lang-4.0/bin/cc','/usr/bin/clang')
replace(sp/'Tree/src/makeGlobalLib','drawTree.c','tree.c')
replace(sp/'ETree/src/transform.c','IVinit(nfront, NULL)','IVinit(nfront, 0)')
subprocess.run(['make','-C',str(sp),'lib'],check=True)
subprocess.run(['make','-C',str(sp/'MT/src'),'makeLib'],check=True)
cc=src/'calculix/CalculiX/ccx_2.23/src'
if not cc.exists():cc=src/'calculix/ccx_2.23/src'
replace(cc/'Makefile','ccx_2.23: $(OCCXMAIN) ccx_2.23.a  $(LIBS)','ccx_2.23: $(OCCXMAIN) ccx_2.23.a')
replace(cc/'readnewmesh.c','*ratiorfnp=ratiorfn;\n  \n  return NULL;','*ratiorfnp=ratiorfn;\n  \n  return;')
for obj in cc.glob('*.o'):obj.unlink()
if (cc/'ccx_2.23.a').exists():(cc/'ccx_2.23.a').unlink()
subprocess.run(['make','-j4','-C',str(cc),'ccx_2.23','CC=/usr/bin/clang','FC=/opt/homebrew/bin/gfortran-15',f'CFLAGS=-O2 -I"{sp}" -DARCH=Linux -DSPOOLES -DARPACK -DMATRIXSTORAGE -DUSE_MT=1','FFLAGS=-O2 -fopenmp -cpp -fallow-argument-mismatch',f'LIBS="{sp}/spooles.a" "{root}/bin/libarpack.a" -framework Accelerate -lpthread -lm'],check=True)
import shutil
shutil.copy2(cc/'ccx_2.23',root/'bin/ccx_2.23')
