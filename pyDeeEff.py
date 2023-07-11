import re


# requires a string
# return a list of tokens, obeying quoted text, split on whitespace
def GetTokens(x):  # standard function for splitting strings containing quoted strings
    return [p for p in
        re.split("( |\\\".*?\\\"|'.*?')", x.strip()) if p.strip()]
# example: words = pyDeeEff.GetTokens(line)


# requires a list of bdf lines
# returns the bottom left corner of the board outline as tuple of floats
def GetOffset(line_list):
    from re import split as split_line
    board = False
    x = []
    y = []
    for line in line_list:
        words = GetTokens(line)
        length = len(words)
        if length == 2 and words[0] == '.BOARD_OUTLINE':
            board = True
        elif length == 4 and board:
            x.append(float(words[1]))
            y.append(float(words[2]))
        elif length == 1 and words[0] == '.END_BOARD_OUTLINE':
            return min(x), min(y)
    return 0, 0  # if board isn't found, return zero zero
# example: x,y = pyDeeEff.GetOffset(bdf_list)


# require a list of sections
# returns the corresponding end section keywords
def GetEndSections(section_list):
    return ['END_' + x for x in section_list]
# example: end_sections = pyDeeEff.GetEndSections(list)


# requires a string, an offset (float), and a conversion factor (float)
# returns a modified string
def OffsetAndConvert(s, offset, units):
    return '%.4f' % ((float(s) - offset) * units)
# example: new_val = pyDeeEff.OffsetAndConvert('0.1234', 1.2. 1.0)


# requires a string representing an angle
# returns a modified string
def RoundOffAngle(s):
    angle = float(s)
    if angle < -89.9 and angle > -90.1:
        return '-90'
    elif angle < -179.9 and angle > -180.1:
        return '-180'
    # needs more angles added
    elif s in ['0.0', '0.00', '0.000', '0.0000']:
        return '0'
    return s
# example: rounded = pyDeeEff.RoundOffAngle('89.999')

# end of pyDeeEff

# version 1.2: added RoundOffAngle
# version 1.4: first github upload
# revision control is now viewed in github rather than the list above
# -----------------------------------------------------------------------------
