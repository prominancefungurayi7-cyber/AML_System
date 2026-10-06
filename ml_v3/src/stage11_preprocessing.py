"""Exactly 32 columns; all learned parameters use Train alone."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import RobustScaler
from stage10a_contract import FEATURES, NAMES

# Positive continuous amounts and heavy-tailed ratios; bounded quantities,
# counts, coverage and topology are deliberately not clipped.
HEAVY=(0,4,17,18,22)
MODES=('raw','clipped','imputed','robust','robust_sentinel')

class Stage11Preprocessor(TransformerMixin,BaseEstimator):
    def __init__(self, mode='raw'): self.mode=mode

    def fit(self,X,y=None):
        assert self.mode in MODES
        x=np.asarray(X,dtype=float)
        assert x.ndim==2 and x.shape[1]==32 and np.isfinite(x).all()
        self.n_features_in_=32
        self.medians_=np.zeros(32); self.bounds_={}; self.missing_counts_={}
        for i,f in enumerate(FEATURES):
            marker=f[7]; mask=np.zeros(len(x),dtype=bool) if marker is None else x[:,i]==marker
            valid=x[~mask,i]
            assert len(valid)>0,f[0]
            self.medians_[i]=np.median(valid); self.missing_counts_[f[0]]=int(mask.sum())
            if i in HEAVY and self.mode in ('clipped','robust','robust_sentinel'):
                self.bounds_[i]=np.quantile(valid,[.005,.995])
        self.scaler_=None
        if self.mode in ('robust','robust_sentinel'):
            self.scaler_=RobustScaler(quantile_range=(25.,75.)).fit(self._base(x))
        return self

    def _base(self,X):
        x=np.array(X,dtype=float,copy=True)
        assert x.shape[1]==32 and np.isfinite(x).all()
        for i,f in enumerate(FEATURES):
            marker=f[7]; mask=np.zeros(len(x),dtype=bool) if marker is None else x[:,i]==marker
            if i in self.bounds_:
                x[~mask,i]=np.clip(x[~mask,i],*self.bounds_[i])
            if self.mode in ('imputed','robust'):
                x[mask,i]=self.medians_[i]
        return x

    def transform(self,X):
        x=self._base(X)
        if self.scaler_ is not None: x=self.scaler_.transform(x)
        assert x.shape[1]==32 and np.isfinite(x).all()
        return x

    def record(self):
        return {'mode':self.mode,'input_count':32,'output_count':32,'feature_order':list(NAMES),
                'fitted_partition':'train','clip_quantiles':[.005,.995],
                'indicators_added':False,'indicator_omission_reason':'Strictly frozen 32-column model input. Imputation loses explicit unavailability; sentinel-preserving comparators retain it.',
                'columns':[{'name':f[0],'marker':f[7],'handling':'none' if f[7] is None else ('train_observed_median' if self.mode in ('imputed','robust') else 'preserved before any scaling'),
                            'train_missing_count':self.missing_counts_[f[0]],'train_observed_median':float(self.medians_[i]),
                            'clip_limits':self.bounds_[i].tolist() if i in self.bounds_ else None,
                            'scaling_center':float(self.scaler_.center_[i]) if self.scaler_ is not None else None,
                            'scaling_range':float(self.scaler_.scale_[i]) if self.scaler_ is not None else None} for i,f in enumerate(FEATURES)]}
