#!/usr/bin/env python

# Copyright 2016 - 2018 Bas van Meerten and Wouter Franssen

# This file is part of ssNake.
#
# ssNake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ssNake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ssNake. If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import scipy.optimize
import scipy.signal


def ent_ffm(missingPoints, fid, posArray):
    fid[posArray] = missingPoints[:len(posArray)] + 1j * missingPoints[len(posArray):]
    spec = np.fft.fft(fid)
    zn = np.fft.fft((np.imag(spec) + 1j * np.real(spec)) / np.abs(spec))
    return (np.sum(np.abs(spec)), np.append(np.imag(zn[posArray]), np.real(zn[posArray])))


def ffm(inp):
    l = len(inp[1])
    res = scipy.optimize.minimize(ent_ffm,
                                  np.zeros(l * 2),
                                  method='L-BFGS-B',
                                  args=inp,
                                  jac=True)
    inp[0][inp[1]] = res['x'][:l] + 1j * res['x'][l:]
    return np.fft.fftshift(np.fft.fft(inp[0]))


def clean(inp):
    residuals = inp[0]
    mask = inp[1]
    gamma = inp[2]
    stopLevel = inp[3]
    maxIter = inp[4]
    replica = np.zeros(len(residuals), dtype=complex)
    for i in range(maxIter):
        findMax = np.argmax(np.abs(residuals))
        maxAmp = residuals[findMax]
        if np.abs(maxAmp) < np.abs(np.mean(residuals)) * stopLevel:
            break
        replica[findMax] += maxAmp * gamma
        residuals -= maxAmp * gamma * np.roll(mask, findMax)
    replica += residuals
    replica = np.real(np.fft.fftshift(replica))
    #Return 'good' spectrum
    return replica


def ist(inp):  # Iterative soft thresholding
    data = inp[0]
    posList = inp[1]  # data points that must be set to zero
    threshold = inp[2]  # level at which the data is cut
    ittnum = inp[3]
    tracelimit = inp[4]  # stoping condition when maximum of residual is below tracelimit*2DMax
    NDmax = inp[5]  # max of ND data. Needed for stopping limit.
    result = np.zeros_like(data, dtype=complex)
    data[0] = data[0] * 0.5
    for itt in range(0, ittnum):
        spectrum = np.real(np.fft.fft(data, axis=0))
        signmatrix = np.sign(spectrum)
        height = np.max(np.abs(spectrum))
        if height < NDmax * tracelimit:  # exit loop if lower limit is reached
            break
        tmpspectrum = np.abs(spectrum) - threshold * height
        tmpspectrum[tmpspectrum < 0] = 0  # Zero all not used parts
        tmpspectrum = signmatrix * tmpspectrum
        result += tmpspectrum
        spectrum -= tmpspectrum
        spectrum = np.conj(scipy.signal.hilbert(spectrum, axis=0))
        data = np.fft.ifft(spectrum, axis=0)
        data[posList] = 0
        
    result = np.real(result + spectrum)

    result = np.fft.fftshift(result,axes=0)
    return result
