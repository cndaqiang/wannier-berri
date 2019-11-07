#
# This file is distributed as part of the Wannier19 code     #
# under the terms of the GNU General Public License. See the #
# file `LICENSE' in the root directory of the Wannier19      #
# distribution, or http://www.gnu.org/copyleft/gpl.txt       #
#                                                            #
# The Wannier19 code is hosted on GitHub:                    #
# https://github.com/stepan-tsirkin/wannier19                #
#                     written by                             #
#           Stepan Tsirkin, University ofZurich              #
#                                                            #
#------------------------------------------------------------

import numpy as np
import fourier 
import lazy_property
from get_data import Data


from utility import  print_my_name_start,print_my_name_end,einsumk

class Data_dk(Data):
    def __init__(self,data,dk=None,AA=None,BB=None,CC=None,SS=None,NKFFT=None):
        self.spinors=data.spinors
        self.iRvec=data.iRvec
        self.real_lattice=data.real_lattice
        self.recip_lattice=data.recip_lattice
        self.NKFFT=data.NKFFT if NKFFT is None else NKFFT
        self.num_wann=data.num_wann

        if dk is not None:
            expdk=np.exp(2j*np.pi*self.iRvec.dot(dk))
            self.dk=dk
        else:
            expdk=np.ones(self.nRvec)
            self.dk=np.zeros(3)
 
        self.HH_R=data.HH_R[:,:,:]*expdk[None,None,:]
        
        for X in ['AA','BB','CC','SS']:
            XR=X+'_R'
            XX=vars()[X]
            if XX in (None,True):
                try:
                    vars(self)[XR]=vars(data)[XR]*expdk[None,None,:,None]
                except KeyError:
                    if XX : raise AttributeError(XR+" is not defined")



    def _rotate(self,mat):
        print_my_name_start()
        return  np.array([a.dot(b).dot(c) for a,b,c in zip(self.UUH_K,mat,self.UU_K)])


    def _rotate_vec(self,mat):
        print_my_name_start()
        res=np.array(mat)
        for i in range(res.shape[-1]):
            res[:,:,:,i]=self._rotate(mat[:,:,:,i])
        print_my_name_start()
        return res

    def _rotate_vec(self,mat):
        print_my_name_start()
        res=np.array(mat)
        for j in range(res.shape[-1]):
            res[:,:,:,:,j]=self._rotate_vec(mat[:,:,:,:,j])
        print_my_name_start()
        return res


    @lazy_property.LazyProperty
    def nbands(self):
        return self.HH_R.shape[0]



    @lazy_property.LazyProperty
    def kpoints_all(self):
        dkx,dky,dkz=1./self.NKFFT
        return np.array([self.dk-np.array([ix*dkx,iy*dky,iz*dkz]) 
          for ix in range(self.NKFFT[0])
              for iy in range(self.NKFFT[1])
                  for  iz in range(self.NKFFT[2])])%1


    @lazy_property.LazyProperty
    def NKFFT_tot(self):
        return np.prod(self.NKFFT)


    @lazy_property.LazyProperty
    def HH_K(self):
        return fourier.fourier_R_to_k(self.HH_R,self.iRvec,self.NKFFT,hermitian=True)


    @lazy_property.LazyProperty
    def E_K(self):
        print_my_name_start()
        EUU=[np.linalg.eigh(Hk) for Hk in self.HH_K]
        E_K=np.array([euu[0] for euu in EUU])
        self._UU_K =np.array([euu[1] for euu in EUU])
        print_my_name_end()
        return E_K


    @lazy_property.LazyProperty
    def UU_K(self):
        self.E_K
        return self._UU_K


    @lazy_property.LazyProperty
    def HHUU_K(self):
        return self._rotate(self.HH_K)


    @lazy_property.LazyProperty
    def delHH_K(self):
        print_my_name_start()
        self.E_K
        delHH_R=1j*self.HH_R[:,:,:,None]*self.cRvec[None,None,:,:]
        return fourier.fourier_R_to_k(delHH_R,self.iRvec,self.NKFFT,hermitian=True)



    @lazy_property.LazyProperty
    def delHHUU_K(self):
        return self._rotate_vec(self.delHH_K)

    @lazy_property.LazyProperty
    def del2HHUU_K(self):
        return self._rotate_vec(self.del2HH_K)

    @lazy_property.LazyProperty
    def delE_K(self):
        print_my_name_start()
        delE_K = np.einsum("klla->kla",self.delHHUU_K)
        check=np.abs(delE_K).imag.max()
        if check>1e-10: raiseruntimeError ("The band derivatives have considerable imaginary part: {0}".format(check))
        return delE_K.real


    @lazy_property.LazyProperty
    def delE_K(self):
        print_my_name_start()
        del2HH=1j*self.delHH_R[:,:,:,:,None]*self.cRvec[None,None,:,None,:]
        del2HH = fourier.fourier_R_to_k(del2HH,self.iRvec,self.NKFFT,hermitian=True)
        del2HH=self._rotate_mat(del2HH)
        del2E_K = np.einsum("klla->kla",del2HH)
        check=np.abs(del2E_K).imag.max()
        if check>1e-10: raiseruntimeError( "The second band derivatives have considerable imaginary part: {0}".format(check) )
        return delE_K.real


    @lazy_property.LazyProperty
    def UU_K(self):
        print_my_name_start()
        self.E_K
        return self._UU_K


    @lazy_property.LazyProperty
    def UUH_K(self):
        print_my_name_start()
        return self.UU_K.conj().transpose((0,2,1))


    @lazy_property.LazyProperty
    def delHH_dE_K(self):
            print_my_name_start()
            _delHH_K_=self.delHHUU_K
            dEig_threshold=1e-14
            dEig=self.E_K[:,:,None]-self.E_K[:,None,:]
            select=abs(dEig)<dEig_threshold
            dEig[select]=dEig_threshold
            _delHH_K_[select]=0
            return -1j*_delHH_K_/dEig[:,:,:,None]

    @lazy_property.LazyProperty
    def delHH_dE_SQ_K(self):
         print_my_name_start()
         return  (self.delHH_dE_K[:,:,:,fourier.beta]
                         *self.delHH_dE_K[:,:,:,fourier.alpha].transpose((0,2,1,3))).imag

#    @lazy_property.LazyProperty
#    def delHH_dE_AA_K(self):
#         return ( (self.delHH_dE_K[:,:,:,fourier.alpha]*self.AAUU_K.transpose((0,2,1,3))[:,:,:,fourier.beta]).imag+
#               (self.delHH_dE_K.transpose((0,2,1,3))[:,:,:,fourier.beta]*self.AAUU_K[:,:,:,fourier.alpha]).imag  )


    @lazy_property.LazyProperty
    def delHH_dE_AA_K(self):
         print_my_name_start()
         return ( (self.delHH_dE_K[:,:,:,fourier.alpha].transpose((0,2,1,3))*self.AAUU_K[:,:,:,fourier.beta]).imag+
               (self.delHH_dE_K[:,:,:,fourier.beta]*self.AAUU_K[:,:,:,fourier.alpha].transpose((0,2,1,3))).imag  )


    @lazy_property.LazyProperty
    def delHH_dE_AA_delHH_dE_SQ_K(self):
         print_my_name_start()
         return ( (self.delHH_dE_K[:,:,:,fourier.alpha].transpose((0,2,1,3))*self.AAUU_K[:,:,:,fourier.beta]).imag+
               (self.delHH_dE_K[:,:,:,fourier.beta]*self.AAUU_K[:,:,:,fourier.alpha].transpose((0,2,1,3))).imag  +
                 (self.delHH_dE_K[:,:,:,fourier.beta]
                         *self.delHH_dE_K[:,:,:,fourier.alpha].transpose((0,2,1,3))).imag  )



    @lazy_property.LazyProperty
    def delHH_dE_BB_K(self):
         print_my_name_start()
         tmp=self.delHH_dE_K.transpose((0,2,1,3))
         return ( (tmp[:,:,:,fourier.alpha] * self.BBUU_K[:,:,:,fourier.beta ]).imag-
                  (tmp[:,:,:,fourier.beta ] * self.BBUU_K[:,:,:,fourier.alpha]).imag  )

#         return ( (self.delHH_dE_K[:,:,:,fourier.alpha]*self.BBUU_K.transpose((0,2,1,3))[:,:,:,fourier.beta]).imag-
#               (self.delHH_dE_K.transpose((0,2,1,3))[:,:,:,fourier.beta]*self.BBUU_K[:,:,:,fourier.alpha]).imag  )

    @lazy_property.LazyProperty
    def delHH_dE_HH_AA_K(self):
         print_my_name_start()
#         return ( np.einsum(  "knl,klma,kmna->kmna",self.HHUU_K,self.AAUU_K[:,:,:,fourier.alpha],self.delHH_dE_K[:,:,:,fourier.beta ]).imag+
#                    np.einsum("kln,kmla,knma->kmna",self.HHUU_K,self.AAUU_K[:,:,:,fourier.beta ],self.delHH_dE_K[:,:,:,fourier.alpha]).imag )
         return np.array([
                  np.einsum("nl,lma,mna->mna",hh,aa[:,:,fourier.alpha],delhh[:,:,fourier.beta ]).imag+
                  np.einsum("ln,mla,nma->mna",hh,aa[:,:,fourier.beta ],delhh[:,:,fourier.alpha]).imag 
                    for hh,aa,delhh in zip(self.HHUU_K,self.AAUU_K,self.delHH_dE_K)])
         
    @lazy_property.LazyProperty
    def delHH_dE_SQ_HH_K(self):
         print_my_name_start()
         return ( np.einsum("kml,knma,klna->klmna",self.HHUU_K,self.delHH_dE_K[:,:,:,fourier.alpha],self.delHH_dE_K[:,:,:,fourier.beta ]).imag ,
                  np.einsum("knm,kmla,klna->klmna",self.HHUU_K,self.delHH_dE_K[:,:,:,fourier.alpha],self.delHH_dE_K[:,:,:,fourier.beta ]).imag ) 

    
    @lazy_property.LazyProperty
    def AAUU_K(self):
        print_my_name_start()
        _AA_K=fourier.fourier_R_to_k( self.AA_R,self.iRvec,self.NKFFT,hermitian=True)
        return self._rotate_vec( _AA_K )


    @lazy_property.LazyProperty
    def BBUU_K(self):
        print_my_name_start()
        _BB_K=fourier.fourier_R_to_k( self.BB_R,self.iRvec,self.NKFFT)
        return self._rotate_vec( _BB_K )
#        return np.einsum("kml,kmna,knp->klpa",self.UUC_K,_BB_K,self.UU_K)


    @lazy_property.LazyProperty
    def CCUU_K_rediag(self):
        print_my_name_start()
        _CC_K=fourier.fourier_R_to_k( self.CC_R,self.iRvec,self.NKFFT)
        _CC_K=self._rotate_vec( _CC_K )
        return np.einsum("klla->kla",_CC_K).real
#        return np.einsum("kml,kmna,knl->kla",self.UUC_K,_CC_K,self.UU_K).real



    @lazy_property.LazyProperty
    def FF_K_rediag(self):
        print_my_name_start()
        _FF_K=fourier.fourier_R_to_k( self.FF_R,self.iRvec,self.NKFFT)
#        return np.einsum("kml,kmna,knl->kla",self.UUC_K,_CC_K,self.UU_K).real
        return np.einsum("kmm->km",_FF_K).imag

    @lazy_property.LazyProperty
    def SSUU_K_rediag(self):
        print_my_name_start()
        _SS_K=fourier.fourier_R_to_k( self.SS_R,self.iRvec,self.NKFFT)
        _SS_K=self._rotate_vec( _SS_K )
#        return np.einsum("kml,kmna,knl->kla",self.UUC_K,_CC_K,self.UU_K).real
        return np.einsum("kmma->kma",_SS_K).real


    @lazy_property.LazyProperty
    def OOmegaUU_K(self):
        print_my_name_start()
        _OOmega_K =  fourier.fourier_R_to_k_hermitian( -1j*(
                        self.AA_R[:,:,:,fourier.alpha]*self.cRvec[None,None,:,fourier.beta ] - 
                        self.AA_R[:,:,:,fourier.beta ]*self.cRvec[None,None,:,fourier.alpha])   , self.iRvec, self.NKFFT )
        return self._rotate_vec(_OOmega_K)
#        return np.einsum("kmi,kmna,knj->kija",self.UUC_K,_OOmega_K,self.UU_K)


    @lazy_property.LazyProperty
    def OOmegaUU_K_rediag(self):
        print_my_name_start()
        return  np.einsum("kiia->kia",self.OOmegaUU_K).real


    @lazy_property.LazyProperty
    def HHOOmegaUU_K(self):
         print_my_name_start()
         return np.einsum("kmn,knma->kma",self.HHUU_K,self.OOmegaUU_K).real


    @lazy_property.LazyProperty
    def HHAAAAUU_K(self):
#        print ("shapes:",self.HHUU_K.shape,self.AAUU_K[:,:,:,fourier.alpha].shape,self.AAUU_K[:,:,:,fourier.beta].shape)
         print_my_name_start()
         return np.einsum("kmi,kina,knma->knma",self.HHUU_K,self.AAUU_K[:,:,:,fourier.alpha],self.AAUU_K[:,:,:,fourier.beta]).imag



unused="""

#    @lazy_property.LazyProperty
#    def UUU_K(self):
#        return self.UU_K[:,:,None,:]*self.UUC_K[:,None,:,:]


    def get_OOmega_K(self):
        try:
            return self._OOmega_K
        except AttributeError:
            print "running get_OOmega_K.."
            self._OOmega_K=    -1j* fourier.fourier_R_to_k( 
                        self.AA_R[:,:,:,fourier.alpha]*self.cRvec[None,None,:,fourier.beta ] - 
                        self.AA_R[:,:,:,fourier.beta ]*self.cRvec[None,None,:,fourier.alpha]   , self.iRvec, self.NKFFT )
             
            return self._OOmega_K


    def get_AA_K(self):
        try:
            return self._AA_K
        except AttributeError:
            print "running get_AA_K.."
            self._AA_K=fourier.fourier_R_to_k( self.AA_R,self.iRvec,self.NKFFT)
            return self._AA_K


"""