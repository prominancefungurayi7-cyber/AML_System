"""Train-only preprocessing for the frozen V2 feature matrix."""
from dataclasses import dataclass
import numpy as np
from sklearn.preprocessing import RobustScaler

# Unbounded counts, values, dispersion, entropy, raw ratios and z-scores.
# Features whose contract constrains them to [0,1] are deliberately absent.
CLIPPED_INDICES=(0,1,2,4,6,7,8,14,16,17,18,19,20,24,26,27)

@dataclass
class TrainPreprocessor:
    clip: bool=False
    scale: bool=False
    quantiles: tuple[float,float]=(0.005,0.995)
    lower: np.ndarray|None=None
    upper: np.ndarray|None=None
    scaler: RobustScaler|None=None

    def fit(self,X):
        X=np.asarray(X,dtype=np.float64)
        if self.clip:
            self.lower=np.quantile(X[:,CLIPPED_INDICES],self.quantiles[0],axis=0)
            self.upper=np.quantile(X[:,CLIPPED_INDICES],self.quantiles[1],axis=0)
        fitted=self._clip(X)
        if self.scale:
            self.scaler=RobustScaler(quantile_range=(25.0,75.0)).fit(fitted)
        return self

    def _clip(self,X):
        out=np.asarray(X,dtype=np.float64).copy()
        if self.clip:
            out[:,CLIPPED_INDICES]=np.clip(out[:,CLIPPED_INDICES],self.lower,self.upper)
        return out

    def transform(self,X):
        out=self._clip(X)
        return self.scaler.transform(out) if self.scale else out

    def fit_transform(self,X): return self.fit(X).transform(X)

    def describe(self,names):
        limits={}
        if self.clip:
            for i,lo,hi in zip(CLIPPED_INDICES,self.lower,self.upper): limits[names[i]]={'lower':float(lo),'upper':float(hi)}
        return {'clip':self.clip,'scale':self.scale,'quantiles':list(self.quantiles) if self.clip else None,
                'clipped_features':limits,'scaler':'RobustScaler(25th/75th percentile)' if self.scale else None,
                'fit_partition':'train'}
