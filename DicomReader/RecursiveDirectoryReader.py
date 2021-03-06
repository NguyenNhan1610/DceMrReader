__author__ = 'medabana'

import dicom
import os

from DicomReader.PatientDirectoryReader import PatientDirectoryReader

class RecursiveDirectoryReader(PatientDirectoryReader):
    """Responsible for reading image data when there is not a DICOMDIR file."""
    def __init__(self, dirNm):
        PatientDirectoryReader.__init__(self, dirNm)
        self._gatherSeriesFileNames(dirNm)

    def _gatherSeriesFileNames(self, dcmDir):
        """ Get the series information, and generate a sorted list of names."""
        self._gatherSeriesFileNamesRecursive(dcmDir)
        seriesSorted = sorted(self._suidAndTimeForProtocols.items(), key=lambda info: info[1])
        for i, series in enumerate(seriesSorted):
            self._protNamesOrdered.append(series[0])

    def _gatherSeriesFileNamesRecursive(self, dirNm):
        """ Search the directory structure recursively and record information about the image series."""
        files = os.listdir(dirNm)
        for file in files:
            fileNm = os.path.join(dirNm, file)
            if not os.path.isdir(fileNm):
                try:
                    protName, suid, time= self._readImFileProtNameSuid(fileNm)
                    if self._fileType == 'NEMA':
                        suid= suid[:-3]
                except:
                    continue  # skip non-dicom file
                if suid not in self._filesForSuid:
                    self._filesForSuid[suid]= [fileNm]
                    self._suidNum += 1
                    protName = str(self._suidNum) + ": " + protName
                    self._suidAndTimeForProtocols[protName] = [suid, time]
                else:
                    self._filesForSuid[suid].append(fileNm)
                # print protName, ": ", fileInfo, " ", suid
            else:
                self._gatherSeriesFileNamesRecursive(fileNm)

    def _readImFileProtNameSuid(self, file):
        """ Get the protocol information from the given file. """
        if self._fileType == 'DICOM' or self._fileType is None:
            try:
                dcm = dicom.read_file(file, stop_before_pixels=False, force=False)
                if self._fileType is None:
                    if 'Enhanced' in str(dcm.SOPClassUID):
                        self._fileType = 'enhancedDICOM'
                    elif 'MR Image' in str(dcm.SOPClassUID):
                        self._fileType = 'DICOM'
            except Exception as why:
                if self._fileType == 'DICOM':
                    # print file + " ", why
                    raise Exception
        if self._fileType == 'NEMA' or self._fileType is None:
            try:
                dcm = dicom.read_file(file, stop_before_pixels=False, force=True)
                try:
                    #need to do this check on all files opened, as the force=True
                    #option will open all sorts of files
                    if dcm.RecognitionCode == 'ACR-NEMA 2.0':
                        if self._fileType is None:
                            self._fileType= 'NEMA'
                        #required for the pixel_array access to work
                        if not dcm.dir('SamplesPerPixel'):
                            dcm.SamplesPerPixel= 1
                except Exception:
                    raise Exception
            except Exception as why:
                    # print file + " ", why
                    raise Exception
        try:
            protName = dcm.SeriesDescription
        except Exception as why:
            # print file + " ", why
            raise Exception
        return protName.lstrip(), dcm.SeriesInstanceUID, self._getImageTime(dcm)

