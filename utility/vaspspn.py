#!/usr/bin/env python2
############################ Wave2spn ###############################
##                                                                 ##
##    An utility to convert WAVECAR to .spn file for WANNIER90     ##
##                                                                 ##
############################ Wave2spn ###############################
#
# Written by Stepan Tsirkin (University of the Basque Country)
#    now at : Iniversity of Zurich

def hlp():
    print """An utility to calculate the .spn file for wannier90 from WAVECAR file generated by VASP
   usage 
	vasp2spn.py -option=value .. 
    -h   print this help message
    
    fin  inputfile  name. default: WAVECAR

    fout outputfile name. default: wannier90.spn

    NB   umber of bands in the output. If NB<=0 all bands are used. default: 0
    
    norm    how to normalize the eigenstates, if they are not perfectly orthonormal
	norm=norm  (D) -   normalize each state individually  
	norm=none      -   do not normalize WFs, take as they are."""
    exit()



writeTXT=False
import sys
from scipy.io import FortranFile
import numpy as np
import datetime

fin="WAVECAR"
fout="wannier90.spn"
NBout=0
normalize="norm"
for arg in sys.argv[1:]:
    if arg=="-h": 
	hlp()
    else:
	k,v=arg.split("=")
	if   k=="fin"  : fin=v
        elif k=="fout" : fout=v
	elif k=="NB"   : NBout=int(v)
	elif k=="norm"   : normalize=v



print "reading {0}\n writing to {1}".format(fin,fout)

WAV=open(fin,"rb")
RECL=3
def record(irec,cnt=np.Inf,dtype=float):
    WAV.seek(irec*RECL)
    return np.fromfile(WAV,dtype=dtype,count=min(RECL,cnt))
#print WAV.read(24)
RECL,ispin,iprec=[int(x) for x in record(0)]

print RECL,ispin,iprec

if iprec!=45200: raise RuntimeError('double precision WAVECAR is not supported')
if ispin!=1 : raise RuntimeError('WAVECAR does not contain spinor wavefunctions. ISPIN={0}'.format(ispin))


NK,NBin=[int(x) for x in record(1,2)]

if  NBout<=0 :NBout=NBin
if  NBout>NBin: print ' WARNING: NBout=',MNout,' exceeds the number of bands in WAVECAR NBin=',NBin,'. We set NBout=',NBmin

print "WAVECAR contains {0} k-points and {1} bands.\n Writing {2} bands in the output".format(NK,NBin,NBout)

SPN=FortranFile(fout, 'w')
header="Created from wavecar at {0}".format(datetime.datetime.now().isoformat())
header=header[:60]
header+=" "*(60-len(header))
SPN.write_record(header) 
SPN.write_record(np.array([NBout,NK],dtype=np.int32))


for ik in xrange (NK):
    npw=int(record(2+ik*(NBin+1),1))
    npw12=npw/2
    if  npw!=npw12*2 : raise RuntimeError ("odd number of coefs {0}".format(npw2))
    print "k-point {0:3d} : {1:6d} plane waves".format(ik,npw)
    WF=np.zeros((npw,NBout),dtype=complex)
    for ib in xrange(NBout):
	WF[:,ib]=record(3+ik*(NBin+1)+ib,npw,np.complex64)
    overlap=WF.conj().T.dot(WF)
    assert np.max(np.abs(overlap-overlap.T.conj()))<1e-15

    if normalize=="norm":
	print "normalizing"
	WF=WF/np.sqrt(np.abs(overlap.diagonal()))

    SIGMA=np.array([[np.einsum("ki,kj->ij",WF.conj()[npw12*i:npw12*(i+1),:],WF[npw12*j:npw12*(j+1),:]) for j in 0,1] for i in 0,1])
    SX=SIGMA[0,1]+SIGMA[1,0]
    SY=-1.j*(SIGMA[0,1]-SIGMA[1,0])
    SZ=SIGMA[0,0]-SIGMA[1,1]
    A=np.array([s[n,m] for m in xrange(NBout) for n in xrange(m+1) for s in SX,SY,SZ],dtype=np.complex128)
#    print A.shape
    print (np.real(np.vstack(  (SX.diagonal(),SY.diagonal(),SZ.diagonal()) )))
    SPN.write_record(A)
    SS=[overlap,SX,SY,SZ]