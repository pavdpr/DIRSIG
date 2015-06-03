function data = readDIRSIGbin( filename, isMac32 )
%READDIRSIGBIN Reads a DIRSIG lidar "bin" file
%
% DESCRIPTION:
%   This function reads a DIRSIG lidar "bin" file and returns a structure
%       with the headers (file, task, and pulse) and the active and passive
%       lidar signals for each pulse.
%
% INPUTS:
%   filename - a string containing the filename (including a path if
%       needed) to the bin file.
%   isMac32 - an optional bool (true/false) variable. Set to true if the
%       bin file was generated with a 32 bit mac build. (allows for the
%       proper number of bytes for the pulse data bytes of the pulse 
%       header. The default is false. This issue was fixed with version 2
%       of the bin file.
%
% OUTPUTS:
%   data - a structure containing the data from the bin file.
%   data.header - the file header
%   data.task - an array of task structures
%   data.task( i ).header - the ith task header
%   data.task( i ).pulse - the ith pulse
%   data.task( i ).pulse( j ).header - the jth pulse header of the ith task
%   data.task( i ).pulse( j ).passive - the passive part of the jth pulse
%       of the ith task. The units are in photons/sec. Use the bin width to
%       convert to photons per time bin. Units are photons/sec
%   data.task( i ).pulse( j ).active - the active (lidar) parts of jth 
%       pulse of the ith task. Units are photons.
%   data.task( i ).pulse( j ).signal - the active and passive parts of the
%       signal for the jth pulse of the ith task. Units are photons. The
%       signal reprents the mean number of photons to reach the detector
%       during that time bin. Appropriate statistics (Poisson?) will need
%       to be used to generate an actual signal.
%   data.task( i ).pulse( j ).time - a time bins x 1 array of the start
%       times of the lidar signal. To convert to a range, multiply by c / 2
%       where c is the speed of light, c~299792458.
%
% HISTORY:
%   2013-02-09: Paul Romanczyk
%     - Initial Version
%   2013-02-11: Paul Romanczyk
%     - Changed pulse header:pulse data type to int32. The documentation
%       at the time had a typo.
%     - Changed the temporal size of the time bin to ( ( bin ct ) * 
%       ( samples/bin ) ) + 1. ( allowing for temporal subsampling ).
%     - Changed from giving a file id to a file name.
%     - Fixed some spelling mistakes in the header.
%   2013-08-21: Paul Romanczyk
%     - Separated the code into separate functions in the same file
%     - Added endian support
%     - Added ability to read in compressed data
%     - Changed the name of the active part of the signal from 'lidar' to
%       'active'
%     - Added beginning of time bins
%   2013-08-22: Paul Romanczyk
%     - Added signal output
%     - Fixed a bug where the time bin beginnings were 0 due to a
%       numerical issue.
%   2013-08-27: Paul Romanczyk
%     - Fixed a bug releated to single pixel detectors not being a 3
%       dimensional array.
%     - Transposed the 3x1 arrays for display purposes
%   2013-08-28: Paul Romanczyk
%     - Transposed the 4x4 affine matrices (they were backwards)
%     - Transposed the 4x4 Mueller matrices (I still need to verify this).
%   2013-09-20: Paul Romanczyk
%     - Transposed the time so it has the same dimensions as a single pixel
%       lidar
%     - Updated some comments for improved ease of use.
%     - Added RIT copyright.
%     - Changed taskNum and pulseNum to tn and pn so the text would fit
%       within 80 characters.
%   2015-03-24: Paul Romanczyk
%     - Fixed the weighting of the passive term.
%
% TODO:
%   1. Make sure the Mueller matrices are properly stored (and not the 
%      transpose of what they should be). I do not know what the correct 
%      order is for this yet.
%
% NOTES:
%   1. The fields of the headers are different between lidar versions. Make
%      sure the field you are looking for exists in the version of the bin
%      file you are using.
%   2. This file may require you to increase the Java Heap Memory to deal 
%      with uncompressing data. Even with turning the Java Heap memory up,
%      I have ran out of memory for a large lidar scan (1000x1000x300 time
%      bins). See the second reference [2] for instructions on how to 
%      increase your Java Heap Memory. It may be necessary to change the 
%      permissions on java.opts so you can write to it.
%
% WARNINGS:
%   This code has not been tested on a version 0 bin file.
%       
% COPYRIGHT:
%   (C) 2013-2015 Rochester Institute of Technology
%
% REFERENCES:
%   [1] http://www.dirsig.org/docs/new/bin.html (Accessed 2013-02-09).
%   [2] "How do I increase the heap space for the Java VM in MATLAB 6.0 
%       (R12) and later versions?" (Accessed 2013-08-21)
%       http://www.mathworks.com/support/solutions/en/data/1-18I2C/
%

fid = fopen( filename, 'r' );

if ( fid < 0 )
    error( [ '"' filename '" is not a valid file.' ] );
end

if ( nargin < 2 )
    % most versions of the bin file will not need this
    isMac32 = false;
end

% read the file header
[ header, endian ] = readDIRSIGbinHeader( fid );

% preallocate the task sizes
task( header.taskCount ).header = '';
for tn = 1:header.taskCount
    % read the task header
    task( tn ).header = readDIRSIGbinTaskHeader( fid, endian );
    
    % read in all of the pulses in the task
    for pn = 1:task( tn ).header.pulseCount;
        % task( taskNum ).pulse( pulseNum ).header = '';
        
        % read the pulse header
        [ task( tn ).pulse( pn ).header, dataTypeSize ] = ...
            readDIRSIGbinPulseHeader( fid, endian, version, isMac32 );
        
        % read the data
        if ( version > 0 )
        [ task( tn ).pulse( pn ).active, ...
            task( tn ).pulse( pn ).passive ] = ...
            readDIRSIGbinPulse( fid, endian, ...
            task( tn ).pulse( pn ).header.pulseDataBytes, ...
            dataTypeSize, ...
            task( tn ).pulse( pn ).header.dataCompressionType, ...
            header.pixelCountX, header.pixelCountX, ...
            task( tn ).pulse( pn ).header.timeBinCount, ...
            task( tn ).pulse( pn ).header.samplesPerTimeBin );
        else
            % version 0 has only 1 sample per time bin
            [ task( tn ).pulse( pn ).active, ...
            task( tn ).pulse( pn ).passive ] = ...
            readDIRSIGbinPulse( fid, endian, ...
            task( tn ).pulse( pn ).header.pulseDataBytes, ...
            dataTypeSize, ...
            task( tn ).pulse( pn ).header.dataCompressionType, ...
            header.pixelCountX, header.pixelCountX, ...
            task( tn ).pulse( pn ).header.timeBinCount, 1 );
        end
        
        % compute the time bin width
        timeBinWidth = ...
            task( tn ).pulse( pn ).header.timeGateStop - ...
            task( tn ).pulse( pn ).header.timeGateStart;
        
        % compute the time of the start of the bin
        task( tn ).pulse( pn ).time = ...
            linspace( ...
            task( tn ).pulse( pn ).header.timeGateStart, ...
            task( tn ).pulse( pn ).header.timeGateStop - ...
            timeBinWidth, ...
            task( tn ).pulse( pn ).header.timeBinCount )';
        
        % compute the signal
        task( tn ).pulse( pn ).signal = ...
            DIRSIGbinSignal( task( tn ).pulse( pn ).active, ...
            task( tn ).pulse( pn ).passive, timeBinWidth );
    end
end

fclose( fid );

data.header = header;
data.task = task;

end



% Function to read a DIRSIG lidar bin file header
function [ fileHeader, endian ] = readDIRSIGbinHeader( fid )
    fileHeader.fileId = char( fread( fid, 11, 'char*1' )' );

    if ( ~strcmp( fileHeader.fileId, 'DIRSIGPROTO' ) )
        fprintf( '%s\n', fileHeader.fileId );
        fclose( fid );
        error( 'The file is NOT a valid DIRSIG lidar file.' );
    end
    fileHeader.version = fread( fid, 1, '*int8' );
    fileHeader.byteOrdering = fread( fid, 1, '*int8' );

    % % set the byteOrder
    endian = 'ieee-be';
    if ( fileHeader.byteOrdering == 1 )
        endian = 'ieee-le'; 
    end


    fileHeader.fileCreationDateTime = ...
        char( fread( fid, 15, 'char*1', endian )' );
    fileHeader.dirsigVersion = char( fread( fid, 32, 'char*1', endian )' );
    if ( fileHeader.dirsigVersion > 2 )
        warning( 'readDIRSIGbin:InvalidBinVersion', ...
            [ 'The current reader only supports up to version 2.\n' ...
            '\tThe values in the output structure are most likely ' ...
            'wrong.' ] );
    end
    fileHeader.sceneDescription = ...
        char( fread( fid, 256, 'char*1', endian )' );
    fileHeader.sceneOriginLatitude = fread( fid, 1, '*double', endian );
    fileHeader.sceneOriginLongitude = fread( fid, 1, '*double', endian );
    fileHeader.sceneOriginHeight = fread( fid, 1, '*double', endian );
    fileHeader.transmitterMountType = ...
        char( fread( fid, 16, 'char*1', endian )' );
    fileHeader.receiverMountType = ...
        char( fread( fid, 16, 'char*1', endian )' );
    fileHeader.pixelCountX = fread( fid, 1, '*uint32', endian );
    fileHeader.pixelCountY = fread( fid, 1, '*uint32', endian );
    fileHeader.pixelPitchX = fread( fid, 1, '*double', endian );
    fileHeader.pixelPitchY = fread( fid, 1, '*double' );
    if ( fileHeader.version > 0 )
        fileHeader.arrayOffsetX = fread( fid, 1, '*double', endian );
        fileHeader.arrayOffsetY = fread( fid, 1, '*double', endian );
        fileHeader.lensDistortionK1 = fread( fid, 1, '*double', endian );
        fileHeader.lensDistortionK2 = fread( fid, 1, '*double', endian );
    end
    fileHeader.taskCount = fread( fid, 1, '*uint32', endian );
    if ( fileHeader.version > 1 )
        fileHeader.focalPlaneId = fread( fid, 1, '*uint16', endian );
    end
end



% function to read a DIRSIG lidar bin task header
function taskHeader = readDIRSIGbinTaskHeader( fid, endian )
    taskHeader.taskDescription = ...
        char( fread( fid, 64, 'char*1', endian )' );
    taskHeader.taskStartDateTime = ...
        char( fread( fid, 15, 'char*1', endian )' );
    taskHeader.taskStopDateTime = ...
        char( fread( fid, 15, 'char*1', endian )' );
    taskHeader.focalLength = ...
        fread( fid, 1, '*double', endian );
    taskHeader.pulseRepetitionFrequency = ...
        fread( fid, 1, '*double', endian );
    taskHeader.pulseDuration = ...
        fread( fid, 1, '*double', endian );
    taskHeader.pulseEnergy = ...
        fread( fid, 1, '*double', endian );
    taskHeader.laserSpectralCenter = ...
        fread( fid, 1, '*double', endian );
    taskHeader.laserSpectralWidth = ...
        fread( fid, 1, '*double', endian );
    taskHeader.pulseCount = ...
        fread( fid, 1, '*uint32', endian );
end



% function to read a DIRSIG lidar bin pulse header
function [ pulseHeader, dataTypeSize ] = ....
    readDIRSIGbinPulseHeader( fid, endian, version, isMac32 )

    pulseHeader.pulseTime = fread( fid, 1, '*double', endian );
    pulseHeader.timeGateStart = fread( fid, 1, '*double', endian );
    pulseHeader.timeGateStop = fread( fid, 1, '*double', endian );
    pulseHeader.timeBinCount = fread( fid, 1, '*uint32', endian );
    if ( version > 0 )
        pulseHeader.samplesPerTimeBin = fread( fid, 1, '*uint32', endian );
    end
    pulseHeader.platformLocation = fread( fid, 3, '*double', endian )';
    if ( version < 2 )
        pulseHeader.platformOrientationAngleOrder = ...
            char( fread( fid, 3, 'char*1', endian )' );
    end
    pulseHeader.platformRotation = fread( fid, 3, '*double', endian )';
    if ( version > 1 )
        pulseHeader.transmiterToMountAffine = ...
            fread( fid, [ 4, 4 ], '*double', endian )';
    else
        pulseHeader.transmiterMountPointingOffset = ...
            fread( fid, 3, '*double', endian )';
        pulseHeader.transmitterOrientationAngleOrder = ...
            char( fread( fid, 3, 'char*1', endian )' );
    end
    pulseHeader.transmitterMountPointingRotation = ...
        fread( fid, 3, '*double', endian )';
    if ( version > 1 )
        pulseHeader.transmitterMountPointingAffine = ...
            fread( fid, [ 4, 4 ], '*double', endian )';
        pulseHeader.receiverToMountAffine = ...
            fread( fid, [ 4, 4 ], '*double', endian )';
    else
        pulseHeader.receiverMountPointingOffset = ...
            fread( fid, 3, '*double', endian )';
        pulseHeader.receiverOrientationAngleOrder = ...
            char( fread( fid, 3, 'char*1', endian )' );
    end
    pulseHeader.receiverMountPointingRotation = ...
        fread( fid, 3, '*double', endian )';
    if ( version > 1 )
        pulseHeader.receiverMountToPlatformAffine = ...
            fread( fid, [ 4, 4 ], '*double', endian )';
    end
    pulseHeader.pulseDataType = fread( fid, 1, '*int32', endian );
    switch pulseHeader.pulseDataType
        case 5
            % double = 8 bytes
            dataTypeSize = 8;
        otherwise
            warning( 'readDIRSIGbin:UnsuportedDataType', ...
                [ '"' num2str( pulseHeader.pulseDataType ) ...
                '" is an unsupported data type' ] );
    end
    pulseHeader.dataCompressionType = ...
        fread( fid, 1, '*int8', endian );
    if ( version < 2 )
        pulseHeader.deltaHistogramFlag = fread( fid, 1, 'char*1', endian );
    else
        % version 2
        pulseHeader.pulseIndex = fread( fid, 1, '*uint32', endian );
    end
    if ( isMac32 && ( version < 2 ) )
        % isMac32 only applies if the version of the bin file is less than
        % 2. Version 2 gaurenteed that this will be 8 bytes.
        % I think I have the right datatype for a mac 32bit mac build
        pulseHeader.pulseDataBytes = fread( fid, 1, '*uint32', endian );
    else
        pulseHeader.pulseDataBytes = fread( fid, 1, '*uint64', endian );
    end
    if ( version > 1 )
        pulseHeader.systemTransmitMuellerMatrix = ...
            fread( fid, [ 4, 4 ], '*double', endian )';
        pulseHeader.systemReceiveMuellerMatrix = ...
            fread( fid, [ 4, 4 ], '*double', endian )';
    end
end



% function to read a DIRSIG lidar bin pulse header
function [ active, passive ] = ...
    readDIRSIGbinPulse( fid, endian, bytes, dataTypeSize, isCompressed, ...
    xPixelCount, yPixelCount, timeBinCount, samplesPerTimeBin )
    
    if ( isCompressed )
        % the compression part of this code was stolen from readPulseData.m
        % from the DIRSIG 4.5.1 (r12800) mac extras section.
        rawData = ...
            fread( fid, double( bytes ), '*uint8' );

        % call zlib via java to decompress
        import com.mathworks.mlwidgets.io.InterruptibleStreamCopier
        a = java.io.ByteArrayInputStream( rawData );
        b = java.util.zip.InflaterInputStream( a );
        isc = InterruptibleStreamCopier.getInterruptibleStreamCopier;
        c = java.io.ByteArrayOutputStream;
        isc.copyStream( b, c );
        tmp = typecast( c.toByteArray, 'double' );
    else
        tmp = fread( fid, bytes / dataTypeSize, '*double', endian );
    end

    % resphape the array
    tmp = reshape( tmp, [ timeBinCount * samplesPerTimeBin + 1, ...
        xPixelCount, yPixelCount ] );
    
    % separate the active and passive parts
    passive = reshape( tmp( 1, :, : ), [ xPixelCount, yPixelCount ] );
    active = tmp( 2:end, :, : );
end



% computes the signal by combining the active and passive terms.
function signal = DIRSIGbinSignal( active, passive, timeBinWidth )
    % The active part has units of photons. The passive part has units of
    % photons/sec. Multiply the passive part by the time bin width to get 
    % the average number of passive photons per time bin.  
    %          signal = active + passive * timeBinWidth                 (1)
    signal = active;
    
    s = size( signal );
    
    switch numel( s )
        case 2
            signal = signal + ( passive * timeBinWidth );
        case 3
            passive = reshape( passive, [ 1, s( 2 ), s( 3 ) ] );
    
            for i = 1:s( 1 )
                signal( i, :, : ) = ...
                    active( i, :, : ) + ( passive .* timeBinWidth );
            end
        otherwise
            error( 'readDIRSIGbin:DIRSIGbinSignal:invalidSize', ...
                'Invalid signal size' );
    end
end