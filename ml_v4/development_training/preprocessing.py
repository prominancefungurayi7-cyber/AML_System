"""Stage18 experimental Train-fitted preprocessing; structured X only."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

CATEGORIES=('wallet_to_wallet','cash_in','cash_out')

class FrozenPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, names, markers, mode='full', dropped=None, only=None):
        self.names=names; self.markers=markers; self.mode=mode; self.dropped=dropped; self.only=only

    def raw(self,x):
        if x.dtype.names!=tuple(self.names):raise ValueError('Frozen semantic order mismatch')
        if not np.isin(x['transaction_type'],CATEGORIES).all():raise ValueError('Unknown type')
        cols=[]; output=[]
        for name in self.names:
            if name==self.dropped or (self.only is not None and name not in self.only):continue
            if name=='transaction_type':
                if self.mode=='missingness':continue
                for cat in CATEGORIES:
                    cols.append((x[name]==cat).astype(float));output.append(name+'='+cat)
            else:
                a=x[name].copy();marker=self.markers.get(name)
                if marker is not None:a[a==marker]=np.nan
                if self.mode=='missingness':a=np.isnan(a).astype(float)
                if np.isinf(a).any():raise ValueError('Infinite input')
                cols.append(a);output.append(name)
        return np.column_stack(cols),output

    def fit(self,x,y=None):
        a,self.output_columns_=self.raw(x)
        self.imputer_=SimpleImputer(strategy='median',keep_empty_features=True,add_indicator=False)
        a=self.imputer_.fit_transform(a)
        self.scaler_=StandardScaler().fit(a)
        self.n_train_rows_=len(x)
        return self

    def transform(self,x):
        a,columns=self.raw(x)
        if columns!=self.output_columns_:raise ValueError('Column mismatch')
        return self.scaler_.transform(self.imputer_.transform(a))
