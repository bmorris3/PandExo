import numpy as np

class ExtractSpec():
    """
    Now that PandExo has several different methods of computing noise, 
    I am creating different classes to handle different noise claculations 
    
    This one extracts the spectrum from the 2d extraction box. It does NOT 
    use the multiaccum noise formula (Rauscher 07). 
    
    Noise Components Included: 
    - Shot
    - Background 
    - Read noise 
    
    """
    def __init__(self, inn, out, rn, timing):
        self.inn = inn
        self.out = out 
        self.exptime_per_int = timing["Exposure Time Per Integration (secs)"]
        self.ngroups_per_int = timing["Num Groups per Integration"]
        self.nocc = timing["Number of Transits"]
        self.nint_out = timing["Num Integrations Out of Transit"]
        self.nint_in = timing["Num Integrations In Transit"]
        self.tframe = timing["Seconds per Frame"]
        self.rn = rn 
    
    def loopingL(self, cen, signal_col, noise_col, bkg_col):
    #create function to find location where SNR is the highest
    #loop from the highest value of the signal downward 
        sn_old= 0
        for ii in range(0,cen+1): #0,1,2,3,4,5 range(0,6).. center=5
            sig_sum = sum(signal_col[cen-ii:cen+1])
            noi_sum = np.sqrt(sum(noise_col[cen-ii:cen+1]))
            bkg_sum = sum(bkg_col[cen-ii:cen+1])
            sn_new = sig_sum/noi_sum
            if sn_old >=sn_new:               
                return cen-ii+1                     
            else:
                sn_old = sn_new
        return 0


    def loopingU(self, cen, signal_col, noise_col, bkg_col):
    #create function to find location where SNR is the highest
    #loop from the highest value of the signal upward
        sn_old= 0
        for ii in range(1,(len(signal_col)-cen+1)): #1,2,3,4,5,6 range(1,6).. center=5, edge =10
            sig_sum = sum(signal_col[cen:cen+ii])
            noi_sum = np.sqrt(sum(noise_col[cen:cen+ii]))
            bkg_sum = sum(bkg_col[cen:cen+ii])
            sn_new = sig_sum/noi_sum

            if sn_old >=sn_new:               
                return cen+ii-1                     
            else:
                sn_old = sn_new
        return len(signal_col)+1 


    def sum_spatial(self, extract_info):    
        """
        Takes extraction info from "extract_retion" and sums pixels in that region 
        takes into account integrations and number of transits 
        """
        nocc = self.nocc
        nint_in = self.nint_in
        nint_out = self.nint_out
        LBout = extract_info['bounds']['LBout']
        LBin = extract_info['bounds']['LBin']
        UBin = extract_info['bounds']['UBin']
        UBout = extract_info['bounds']['UBout']
        photon_sig_in = extract_info['photons']['photon_sig_in']    
        photon_sig_out = extract_info['photons']['photon_sig_out']
        var_pix_in = extract_info['photons']['var_pix_in']
        var_pix_out = extract_info['photons']['var_pix_out']
        photon_sky_in = extract_info['noise']['photon_sky_in']
        photon_sky_out = extract_info['noise']['photon_sky_out']
        rn_var_in = extract_info['noise']['rn_var_in']
        rn_var_out = extract_info['noise']['rn_var_out']


        rr, lenw = photon_sig_in.shape

        # sum spectrum in the spatial direction to create 1d spectrum 
        photon_out_1d = range(0,lenw)
        photon_in_1d = range(0,lenw)
        var_out_1d = range(0,lenw)
        var_in_1d = range(0,lenw)
        sky_in_1d = range(0,lenw)
        sky_out_1d = range(0,lenw)
        rn_in_1d = range(0,lenw)
        rn_out_1d = range(0,lenw)


        #sum 2d spectrum in extraction region in spatial direciton to create 1d spec
        for i in range(0,lenw):
            photon_out_1d[i] = sum(photon_sig_out[LBout[i]:UBout[i],i])*nint_out*nocc
            photon_in_1d[i] = sum(photon_sig_in[LBout[i]:UBout[i],i])*nint_in*nocc
            var_out_1d[i] = sum(var_pix_out[LBout[i]:UBout[i],i])*nint_out*nocc
            var_in_1d[i] = sum(var_pix_in[LBout[i]:UBout[i],i])*nint_in*nocc
            sky_out_1d[i] = sum(photon_sky_out[LBout[i]:UBout[i],i])*nint_out*nocc
            sky_in_1d[i] = sum(photon_sky_in[LBout[i]:UBout[i],i])*nint_in*nocc
            rn_out_1d[i] = sum(rn_var_out[LBout[i]:UBout[i],i])*nint_out*nocc
            rn_in_1d[i] = sum(rn_var_in[LBout[i]:UBout[i],i])*nint_in*nocc


        photon_out_1d = np.array(photon_out_1d)
        photon_in_1d = np.array(photon_in_1d)
        var_out_1d = np.array(var_out_1d)
        var_in_1d = np.array(var_in_1d)
        sky_in_1d = np.array(sky_in_1d)
        sky_out_1d = np.array(sky_out_1d)
        rn_out_1d = np.array(rn_out_1d)
        rn_in_1d = np.array(rn_in_1d)

        return {'photon_out_1d':photon_out_1d, 'photon_in_1d':photon_in_1d, 
                'var_in_1d':var_in_1d, 'var_out_1d':var_out_1d, 'rn_in_1d':rn_in_1d,
                'rn_out_1d':rn_out_1d,'sky_in_1d': sky_in_1d, 'sky_out_1d': sky_out_1d, 
                'extract_info':extract_info}

    def extract_region(self): #second to last 
        """
        Contains functionality to extract spectra from the 2d images. 
        MULITACCUMM currently not accounted for. 
        
        attricutes: 
            LoopingL: finds extraction box based on optimal SNR  
            LoopingU: finds extraction box based on optimal SNR  
        """
        inn = self.inn
        out = self.out
        exptime_per_int = self.exptime_per_int
        ngroups_per_int = self.ngroups_per_int
        #Full variance including all noise sources
        detector_var=out.noise.var_pix
        #Standard deviation (i.e. sqrt(detector_var))
        detector_stdev=out.noise.stdev_pix

        #signal (no noise no background)
        s_out = out.signals[0].rate 
        s_in = inn.signals[0].rate 

        #size of wavelength direction 
        rr,lenw = s_out.shape

        #background 
        bkgd_out = out.signals[0].rate_plus_bg - out.signals[0].rate
        bkgd_in = inn.signals[0].rate_plus_bg - inn.signals[0].rate


        #define psf center based on max value on detector
        cenRo,cenCo = np.unravel_index(s_out.argmax(), s_out.shape)
        cenRi,cenCi = np.unravel_index(s_out.argmax(), s_in.shape)

        #define out of transit parameters to calculate extraction region

        #multiaccum sample data factor 
        factor_flux = 1.0 #6.0/5.0*(ngroups_per_int**2.0+1.0)/(ngroups_per_int**2.0+ngroups_per_int)
        factor_rn = 1.0 #12.0*(ngroups_per_int-1.0)/(ngroups_per_int**2.0 + ngroups_per_int)

        photon_sig_out = s_out*exptime_per_int*factor_flux #total photons per pixel in signal
        photon_sky_out = bkgd_out*exptime_per_int*factor_flux #total photons per pixel in background 
        #variance stricly due to detector readnoise.. You might think this is 
        #wrong because usually RN isnt multiplie by time.. but Pandeia gives RN in rms/ sec. 
        rn_var_out= out.noise.var_rn_pix*exptime_per_int*factor_rn 
        var_pix_out = photon_sig_out + photon_sky_out + rn_var_out # variance of noise per pixel

        #define parameters for IN transit 
        photon_sig_in = s_in*exptime_per_int*factor_flux #total photons per pixel in signal
        photon_sky_in = bkgd_in*exptime_per_int*factor_flux #total photons per pixel in background 
        rn_var_in= inn.noise.var_rn_pix*factor_rn #variance stricly due to detector readnoise
        var_pix_in = photon_sig_in + photon_sky_in + rn_var_in # variance of noise per pixel 

        UBout = range(0,lenw)
        LBout = range(0,lenw)
        UBin = range(0,lenw)
        LBin = range(0,lenw)


        #start new loop over column
        for j in range(0,lenw):

            #define column of interest
            noise_col_out = var_pix_out[:, j]
            signal_col_out = photon_sig_out[:,j]
            bkg_col_out = photon_sky_out[:,j]
            rn_col_out = rn_var_out[:,j]

            noise_col_in =  var_pix_in[:, j]
            signal_col_in = photon_sig_in[:,j]
            bkg_col_in = photon_sky_in[:,j]


            #store lower and upper bound extraction regions for in and out of transit 
            LBout[j] = self.loopingL(cenRo, signal_col_out, noise_col_out, bkg_col_out)
            UBout[j] = self.loopingU(cenRo, signal_col_out, noise_col_out, bkg_col_out)
            LBin[j] = self.loopingL(cenRi, signal_col_in, noise_col_in, bkg_col_in    )
            UBin[j] = self.loopingU(cenRi, signal_col_in, noise_col_in, bkg_col_in)

        #this could be made more elegant later... not very efficient 
        noise = {'rn_var_out':rn_var_out, 'rn_var_in':rn_var_in, 
                 'photon_sky_in':photon_sky_in, 'photon_sky_out': photon_sky_out }
        bounds = {'LBout':LBout, 'UBout':UBout, 'LBin':LBin, 'UBin':UBin}
        photons = {'photon_sig_out': photon_sig_out, 'photon_sig_in':photon_sig_in, 
                   'var_pix_in':var_pix_in,'var_pix_out': var_pix_out}
        extract_info ={'bounds':bounds, 'photons':photons, 'noise':noise}

        return extract_info

    def run_2d_extract(self):
        """
            Contains functionality to extract noise from 2d detector image

            Attributes:
                extract_region 
                sum_spatial 
        """
        #optimize SNR and extract region 
        extract = self.extract_region()
        #return summed up pixels 
        return self.sum_spatial(extract)
        
        
    def run_slope_method(self): 
        """
        contains functionality to compute noise using Pandeia 1d noise 
        output products (uses MULTIACCUM) noise formula 
        """
        curves_out = self.out.curves
        curves_inn = self.inn.curves
        noccultations = self.nocc
        #In the following the SN is changed to incorporate number of occultations 
        #i.e. multiply by sqrt(n) 
        sn_in = curves_inn['sn'][1]*np.sqrt(noccultations)
        sn_out = curves_out['sn'][1]*np.sqrt(noccultations)

        extracted_flux_inn = curves_inn['extracted_flux'][1]
        extracted_noise_inn = curves_inn['extracted_flux'][1]/(sn_in)

        extracted_flux_out = curves_out['extracted_flux'][1]
        extracted_noise_out = curves_out['extracted_flux'][1]/(sn_out)

        #units of this unconventional.. sigma/s
        #because snr = extracted flux / extracted noise and 
        #extracted flux in units of electrons /s
        varin = (extracted_noise_inn)**2.0
        varout = (extracted_noise_out)**2.0

        return {'photon_out_1d':extracted_flux_out, 'photon_in_1d':extracted_flux_inn, 
                    'var_in_1d':varin, 'var_out_1d': varout}
    
    
    def run_f_minus_l(self):
        """
        Uses 1d exracted products from pandeia to compute noise without 
        multiaccum noise formula from Rauscher 07 
        
        Uses robberto 2009 formula to compute readnoise (taken from 2d 
        pandeia output). 1d readnoise is used by summing over entire postage stamp. 
        Pandeia will use entire extraction region but if not this could just slightly 
        over estimate read noise. 
        
        """
        inn = self.inn
        curves_out = self.out.curves
        curves_inn = self.inn.curves
        
        
        #on source out versus in 
        on_source_in = self.tframe * (self.ngroups_per_int-1.0) * self.nint_in
        on_source_out = self.tframe * (self.ngroups_per_int-1.0) * self.nint_out

        #calculate rn 
        rn_var = self.rn**2.
        postage_size = inn.noise.var_rn_pix.shape
        #1d rn       rn/pix * #pixs    *two reads (first & last) * # of integrations *nocc
        rn_var_inn = rn_var * postage_size[0] * 2.0 * self.nint_in * self.nocc
        rn_var_out = rn_var * postage_size[0] * 2.0 * self.nint_out * self.nocc

        #extract fluxs
        extracted_flux_inn = curves_inn['extracted_flux'][1] * on_source_in * self.nocc
        extracted_flux_out = curves_out['extracted_flux'][1] * on_source_out * self.nocc
                
        #background + contamination extracted 
        bkg_flux_inn = curves_inn['extracted_bg_total'][1] * on_source_in * self.nocc
        bkg_flux_out = curves_out['extracted_bg_total'][1] * on_source_out * self.nocc
        
        #total nois 
        varin = extracted_flux_inn + bkg_flux_inn + rn_var_inn
        varout = extracted_flux_out + bkg_flux_out + rn_var_out
        
        return {'photon_out_1d':extracted_flux_out, 'photon_in_1d':extracted_flux_inn, 
                    'var_in_1d':varin, 'var_out_1d': varout}
    
    
    
    
    
    
    