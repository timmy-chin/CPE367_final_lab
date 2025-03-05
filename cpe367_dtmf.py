#!/usr/bin/python

import sys
from cpe367_sig_analyzer import cpe367_sig_analyzer
from my_fifo import my_fifo

M = 8  # window size
C = 25  # rounder
threshold = 31  # output threshold
rows = [697, 770, 852, 941]  # row tone frequency
columns = [1209, 1336, 1477, 1633]  # colum tone frequency


def build_dial_table():
    dials = [
        [1, 2, 3, "A"],
        [4, 5, 6, "B"],
        [7, 8, 9, "C"],
        ["*", 0, "#", "D"]
    ]

    dial_table = {}
    for row, dial in zip(rows, dials):
        inner_table = {}
        for column, num in zip(columns, dial):
            inner_table[column] = num
        dial_table[row] = inner_table

    return dial_table

def tone_with_max_output(xin, tones, filters, s2, n_curr):
    filter_max_outputs = []  # store all filter max outputs in window
    for i in range(len(filters)):
        b0, a1, a2, fifo = filters[i]  # get coefficients for the ith filter
        y = (b0 * xin + a1 * fifo.get(0) + a2 * fifo.get(1)) / C  # calculate filter output
        fifo.update(y)  # store output for future
        s2.set(f'sig_{tones[i]}', n_curr, y / C)  # Plot ith tone signal

        # Get max filter output in window
        max_value = max([abs(fifo.get(k)) for k in range(M)])
        filter_max_outputs.append(max_value)

    max_output = max(filter_max_outputs)  # max output of all 4 filters
    if max_output < threshold:
        return -1  # no tone found

    max_tone_index = filter_max_outputs.index(max_output)  # get index of filter with the max output
    return tones[max_tone_index]  # return the tone frequency of the filter


############################################
############################################
# define routine for detecting DTMF tones
def process_wav(fpath_sig_in):


    ###############################
    # define list of signals to be displayed by and analyzer
    #  note that the signal analyzer already includes: 'symbol_val','symbol_det','error'
    more_sig_list = ['sig_697', 'sig_770', 'sig_852', 'sig_941',
                     'sig_1209', 'sig_1336', 'sig_1477', 'sig_1633']

    # sample rate is 4kHz
    fs = 4000

    # instantiate signal analyzer and load data
    s2 = cpe367_sig_analyzer(more_sig_list,fs)
    s2.load(fpath_sig_in)
    s2.print_desc()

    ########################
    # students: setup filters

    #  setup for tones and filters for row
    symbol_table = build_dial_table()

    row_tones = rows
    rows_filters = [
        (round(C * 0.1), round(C * 0.8247), round(C * -0.8101), my_fifo(3)),  # 697 Hz
        (round(C * 0.1), round(C * 0.6363), round(C * -0.8101), my_fifo(3)),  # 770 Hz
        (round(C * 0.1), round(C * 0.4147), round(C * -0.8101), my_fifo(3)),  # 852 Hz
        (round(C * 0.1), round(C * 0.1666), round(C * -0.8101), my_fifo(3))  # 941 Hz
    ]

    column_tones = columns
    column_filters = [
        (round(C * 0.1), round(C * -0.5804), round(C * -0.8101), my_fifo(3)),  # 1209 Hz
        (round(C * 0.1), round(C * -0.9065), round(C * -0.8101), my_fifo(3)),  # 1336 Hz
        (round(C * 0.1), round(C * -1.2260), round(C * -0.8101), my_fifo(3)),  # 1477 Hz
        (round(C * 0.1), round(C * -1.5091), round(C * -0.8101), my_fifo(3))  # 1633 Hz
    ]

    # process input
    for n_curr in range(s2.get_len()):

        # read next input sample from the signal analyzer
        xin = int(round(C * s2.get('xin', n_curr)))  # Scale input to integer space
        row_tone = tone_with_max_output(xin, row_tones, rows_filters, s2, n_curr)  # detect row tone
        column_tone = tone_with_max_output(xin, column_tones, column_filters, s2, n_curr)  # detect column tone

        ########################
        # students: evaluate each filter and implement other processing blocks

        ########################
        # students: combine results from filtering stages
        #  and find (best guess of) symbol that is present at this sample time
        if row_tone == -1 or column_tone == -1:
            symbol_val_det = -1  # no symbol found
        else:
            symbol_val_det = symbol_table[row_tone][column_tone]  # get symbol from table


        # save detected symbol
        s2.set('symbol_det',n_curr,symbol_val_det)

        # get correct symbol (provided within the signal analyzer)
        symbol_val = s2.get('symbol_val',n_curr)

        # compare detected signal to correct signal
        symbol_val_err = 0
        if symbol_val != symbol_val_det: symbol_val_err = 1

        # save error signal
        s2.set('error',n_curr,symbol_val_err)


    # display mean of error signal
    err_mean = s2.get_mean('error')
    print('mean error = '+str( round(100 * err_mean,1) )+'%')

    # define which signals should be plotted
    plot_sig_list = ['sig_697', 'sig_770', 'sig_852', 'sig_941',
                     'sig_1209', 'sig_1336', 'sig_1477', 'sig_1633',
                     'symbol_val', 'symbol_det', 'error']

    # plot results
    s2.plot(plot_sig_list)

    return True


############################################
############################################
# define main program
def main(argv):
    # check python version!
    major_version = int(sys.version[0])
    if major_version < 3:
        print('Sorry! must be run using python3.')
        print('Current version: ')
        print(sys.version)
        return False

    # assign file name from command line
    fpath_sig_in = argv[1]
    # fpath_sig_in = "dtmf_signals_slow.txt"
    # fpath_sig_in = "dtmf_signals_fast.txt"

    # let's do it!
    return process_wav(fpath_sig_in)

############################################
############################################
# call main function
if __name__ == '__main__':

    main(sys.argv)
    quit()
