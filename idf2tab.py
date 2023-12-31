import os
import pyperclip
import pyDeeEff

# user settings
extensions = {'.emn': '.emn', '.emp': '.emp'}  # extension list, before and after (note that FreeCAD doesn't accept bdf)
sections = ['HEADER','BOARD_OUTLINE','PLACEMENT','DRILLED_HOLES','ELECTRICAL','MECHANICAL']  # all other sections will be removed
outline = ['0',]  # list of loop identifiers to include, such as '0' or '0','1' or '*' to include ALL
include = ['U1', 'U2', 'U3', 'U4', 'U5',]  # list of components to include
ifilter = ['*',]  # list of component prefixes to include: single letter 'U','J',etc or '*' to include ALL
exclude = ['J2','J7']  # list of components to exclude regardless of include filters
exclude_bottom = True  # set to False (include bottomside components that pass the filter) or True (exclude them ALL, even ones in the filter)
refdes_suffix = "_"  # attempt to fix freecad bug with naming
thickness = 1.57   # thickness in mm, set to -1 to keep original thickness
min_pth = 0.4  # via size limit in mm, anything equal or larger gets included in PWB

# preparation
allFiles = os.listdir('.')  # get list of files/folders in current folder
fileList = [x for x in allFiles if x[-4:] in extensions and not x.startswith('idf2tab')]  # filter list based on extension, skip files generated by this script
log = '\n'.join(fileList) + '\n\n'  # string for storing log file, start with file list
units = 1.0  # gets auto-set to something else if file is in THOU
outtab = ''   # string for storing tab version, appended by every file rather than being reset each iteration
end_sections = pyDeeEff.GetEndSections(sections)  # names of end keywords based on list provided above


def keep(s):
    r = False  # default to not kept
    if s in include or s[0] in ifilter or '*' in ifilter:
        r = True
    if s in exclude:
        r = False
    return r


def libfix(s):
    if line.endswith('40.00'):  # default height set by Pactron in Allegro
        if line.startswith('85OHM'):
            return line[:-5] + '2.0'
        elif line.startswith('80-OHM'):
            return line[:-5] + '2.1'
        elif line.startswith('FIDUCIAL'):
            return line[:-5] + '2.2'
        elif line.startswith('SENSE_PAD'):
            return line[:-5] + '2.3'
        elif line.startswith('KELVIN'):
            return line[:-5] + '2.4'
        elif line.startswith('SMD_40P'):
            return line[:-5] + '2.5'
        elif line.startswith('80OHMDDR'):
            return line[:-5] + '2.6'
        else:
            print(line)  # is this a TP? TP_5010 5010 THOU 320.00
    return line


for f in fileList:
    outlist = []  # list for storing output file lines
    output = ''   # string for storing output file
    count = {}    # blank dictionary for counting tokens per line

    # input and output
    log = log + 'Reading ' + f + '\n'  # log the input filename
    with open(f, 'r') as infile:
        lines = infile.read().splitlines()  # read lines
    # standard version of outfile:
    # outfile = 'idf2tab (' + f[:-4] + ')' + extensions[f[-4:]]
    # FreeCAD version of outfile, ONLY works for one file pair at a time:
    outfile = 'idf2tab' + extensions[f[-4:]]

    # pass the list of lines, get offset XY, add to log
    xoffset, yoffset = pyDeeEff.GetOffset(lines)
    zoffset = 0.0  # probably won't get used
    log = log + '   Offsets: ' +  '%.2f' % xoffset + ', ' + '%.2f' % yoffset + '\n'

    keep_next_line = False
    for line in lines:
        line = libfix(line)  # correct height errors in library file
        words = pyDeeEff.GetTokens(line)  # split into tokens, keeps quotes (but google strips them later)
        length = len(words)  # length of list of words
        if words[0][1:] in sections:  # check for first word (minus the '.') being a keyword
            section = words[0][1:]
        if section == 'HEADER' and len(words) == 2:  # this line contains the filename and units
            words[0] = outfile  # set project name to file name
            if words[1] == 'THOU':
                units = 25.4/1000
                words[1] = 'MM'
                log = log + '   Conversion factor: ' + str(units) + '\n'
        if section == 'HEADER' and len(words) == 5 and words[2].startswith('allegro'):  # brd or lib, middle word is system name
            words[2] = 'pyDeeEff'  # replace with script name
        if section == 'BOARD_OUTLINE':
            if len(words) == 1 and thickness > 0.0 and not words[0].startswith('.'):
                words[0] = '%.2f' % thickness
            if len(words) == 4:
                # print(words)
                words[1] = pyDeeEff.OffsetAndConvert(words[1], xoffset, units)
                words[2] = pyDeeEff.OffsetAndConvert(words[2], yoffset, units)
                words[3] = pyDeeEff.RoundOffAngle(words[3])
                if words[0] in outline or '*' in outline:
                    pass  # keep entry because it's in the list
                else:
                    words = ['line has been removed',]  # remove entry
        if section == 'DRILLED_HOLES':
            if len(words) == 7:  # defines a hole
                dia = float(words[0]) * units
                if dia < min_pth:
                    words = ['line has been removed',]  # empty list so it doesn't get added
                else:
                    words[0] = pyDeeEff.OffsetAndConvert(words[0], 0.0,     units)
                    words[1] = pyDeeEff.OffsetAndConvert(words[1], xoffset, units)
                    words[2] = pyDeeEff.OffsetAndConvert(words[2], yoffset, units)
        if section == 'PLACEMENT':
            if words[0][1:] in sections or words[0][1:] in end_sections:  # keep the keywords
                pass
            elif keep_next_line:  # was set last loop
                keep_next_line = False  # unset for next loop
                words[0] = pyDeeEff.OffsetAndConvert(words[0], xoffset, units)
                words[1] = pyDeeEff.OffsetAndConvert(words[1], yoffset, units)
                words[2] = pyDeeEff.OffsetAndConvert(words[2], zoffset, units)
                if words[4] == 'BOTTOM' and exclude_bottom:
                    outlist.pop()  # remove last line from output list
                    words = ['line has been removed',]  # empty list so it doesn't get added
            elif len(words) == 3 and keep(words[2]):  # refdes is to be kept
                keep_next_line = True  # keep next line as well
                words[2] = words[2] + refdes_suffix  # add optional suffix
            else:
                words = ['line has been removed',]  # empty list so it doesn't get added
        try:
            count[length] = count[length] + 1  # add one to counter
        except:
            count[length] = 1  # start new counter
        if section == '' or words[0] == 'line has been removed':
            pass  # skip line, may use later
        else:
            outlist.append(words)  # add good lines to output list
        if words[0][1:] in end_sections:  # check for first word (minus the '.') being a keyword
            section = ''
    log = log + '   ' + str(count) + '\n'
    for words in outlist:
        output = output + ' '.join(words) + '\n'  # join with spaces
        outtab = outtab + '\t'.join(words) + '\n'  # join with tabs
    log = log + 'Writing ' + outfile + '\n\n'  # log the output filename with an extra CRLF
    with open(outfile, 'w') as outfile:
        outfile.write(output)

with open('idf2tab.log', 'w') as logfile:
    logfile.write(log)

pyperclip.copy(outtab)  # put all data on clipboard


# version history
# 1.0 - first version in google drive, supports lib file
# 1.1 - added more to pyDeeEff
# 1.2 - stopped using bdf for output because of FreeCAD
#       excluded files generated by this script from the file list
# 1.3 - replaced filename in 2nd header line
#       added exclude_bottom option, and ifilter = '*' to include all
# 1.4 - moved zoffset into loop for no reason
# 1.5 - system name is now overwritten with pyDeeEff
# revision control is now viewed in github rather than the list above
# -----------------------------------------------------------------------------
