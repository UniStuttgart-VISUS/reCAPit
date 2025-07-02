import numpy as np
import pandas as pd

from scipy.ndimage import gaussian_filter1d
from scipy.signal import decimate
from PyQt6.QtCore import QObject, pyqtSlot

    
def preprocess_signals(signals):
    merged = np.sum(signals, axis=0)
    upper_bound = np.percentile(merged, 99.999)
    signals = [np.clip(s / upper_bound, 0, 1) for s in signals]
    return signals


def compute_stacks(signals):
    stacked_signals = []

    for s in signals:
        accu_signal = np.array(s, copy=True)
        if len(stacked_signals) > 0:
            accu_signal += stacked_signals[-1]
        stacked_signals.append(accu_signal)

    return stacked_signals


def permute(values, perm):
    return [values[idx] for idx in perm]


class StackedSeries(QObject):
    pass

class StackedSeries(QObject):
    def __init__(self, stacks, signals, labels, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.stacks = stacks
        self.labels = labels
        self.labels_active = labels.copy()

    @classmethod
    def empty(cls, labels, min_ts, max_ts):
        signals = pd.DataFrame()
        signals['timestamp [sec]'] = np.linspace(min_ts, max_ts, 100)
        for l in labels:
            signals[l] = np.zeros_like(signals['timestamp [sec]'])

        #stacks = {l: np.ones_like(signals['timestamp [sec]']) for l in labels}
        return cls(signals, signals, labels)

    def recompute(self, active_labels):
        preprocessed = []
        for label in self.labels:
            if label in active_labels:
                sig = np.array(self.stacks[label + '_pre'].values, copy=True)
            else:
                sig = np.zeros_like(self.stacks[label + '_pre'].values)

            preprocessed.append(sig)

        signal_stacks = compute_stacks(preprocessed)

        for label, stack in zip(self.labels, signal_stacks):
            self.stacks[label] = stack

    @classmethod
    def from_signals(cls, signals, min_ts, max_ts, labels, downsampling_factor, log_transform=False, log_factor=1e9):
        out = pd.DataFrame()
        signals['timestamp [sec]'] = np.linspace(min_ts, max_ts, len(signals.index))

        downsampled = [signals[label].values for label in labels] 

        if log_transform:
            downsampled = [np.log(1 + log_factor*s) for s in downsampled] 
            #downsampled = [gaussian_filter1d(s, 20) for s in downsampled] 

        downsampled = [decimate(s, downsampling_factor) for s in downsampled] 
        preprocessed = preprocess_signals(downsampled)
        signal_stacks = compute_stacks(preprocessed)

        for label, stack, pre in zip(labels, signal_stacks, preprocessed):
            out[label] = stack
            out[label + '_pre'] = pre

        out['timestamp [sec]'] = np.linspace(min_ts, max_ts, len(out.index))

        return cls(stacks=out, signals=signals, labels=labels)

        
    @pyqtSlot(result='QVariantMap')
    def LabelDistribution(self):
        #return {l: float(self.signals[l].mean().item()) for l in self.labels}
        return {l: float(self.signals[l].mean()) for l in self.labels_active}
        total = 0
        #total = self.signals['timestamp [sec]'].iloc[-1] - self.signals['timestamp [sec]'].iloc[0]
        distr = {}

        for l in self.labels:
            distr[l] = self.signals[l].sum()
            total += distr[l]

        if total < 1e-12:
            total = 1

        return {k: float(v.item() / total)for k, v in distr.items()}


    @pyqtSlot(float, float, result=StackedSeries)
    def slice(self, start_ts, end_ts):
        start_index = self.stacks[self.stacks['timestamp [sec]'] < start_ts].index[-1] if not self.stacks[self.stacks['timestamp [sec]'] < start_ts].empty else None
        mask_stacks = (self.stacks['timestamp [sec]'] >= start_ts) & (self.stacks['timestamp [sec]'] <= end_ts)
        mask_signals = (self.signals['timestamp [sec]'] >= start_ts) & (self.signals['timestamp [sec]'] <= end_ts)
        #mask = (self.stacks['timestamp [sec]'] >= start_ts) & (self.stacks['timestamp [sec]'] <= end_ts)

        if start_index is not None:
            mask_stacks[start_index] = True

        return StackedSeries(self.stacks[mask_stacks], self.signals[mask_signals], self.labels_active, parent=self)
            
    @pyqtSlot(int, int, int, result=str)
    def StackAsSvgPath(self, index, width, height):
        index = len(self.labels_active) - index - 1
        target_stack = self.stacks[self.labels_active[index]].values

        xv = np.linspace(0, width, target_stack.shape[0])
        yv = height * target_stack

        if target_stack.shape[0] == 0:
            return ""

        cstr = f"M 0 0 L 0 {yv[0]:.4f}"

        if target_stack.shape[0] < 4:
            for j in range(0, len(xv)):
                cstr += f"L {xv[j]:.4f} {yv[j]:.4f}"
        else:
            cstr += f"C {xv[0]:.4f} {yv[0]:.4f}, {xv[1]:.4f} {yv[1]:.4f}, {xv[2]:.4f} {yv[2]:.4f}"
            for j in range(3, len(xv)-1, 2):
                cstr += f"S {xv[j]:.4f} {yv[j]:.4f}, {xv[j+1]:.4f} {yv[j+1]:.4f}"
            cstr += f"L {xv[-1]:.4f} {yv[-1]:.4f}"
        
        cstr += f"L {xv[-1]:.4f} 0 Z"
        return cstr


    @pyqtSlot(int, result=str)
    def Label(self, index):
        index = len(self.labels_active) - index - 1
        return self.labels_active[index]


    @pyqtSlot(result=int)
    def StackCount(self):
        return len(self.labels_active)
