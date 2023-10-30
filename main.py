from nfstream import (
    NFStreamer,
    NFPlugin
)
from pympler import asizeof
from psutil import (
    cpu_percent,
    virtual_memory,
    Process
)
import argparse
from os import (
    path,
    getpid
)
import configparser
from time import sleep
from datetime import datetime
import ast
import buffer
import plt_graphics

dirname = path.dirname(__file__)
entries = []
bufferArray = []
ARU = []
(TCh_t0, TCh_t1) = (None, None)
(ARU_t0, ARU_t1) = (None, None)
T = None
originalBufferSize = 0
(input_params, exporter) = (None, None)


class FlowSlicer(NFPlugin):
    """
    This plugin will slice flows based on the number of packets. Overloads on_init and on_update methods.
    """

    counter = 1

    def on_init(self, packet, flow):
        if self.limit == 1:
            flow.expiration_id = -1

    def on_update(self, packet, flow):
        if self.limit == flow.bidirectional_packets:
            flow.expiration_id = -1


def capture(dl, source, is_flow_slicer: bool = False) -> None:
    """
    Capture packets from a given source and process them. If is_flow_slicer is True, then the FlowSlicer plugin will be
    used to slice flows based on the number of packets. Otherwise, the default behavior is excepted using the
    NFStream library.

    :param dl: delete list
    :param source: source of the capture
    :param is_flow_slicer: True if the FlowSlicer plugin should be used, False otherwise
    :return: None
    """
    global bufferArray
    global originalBufferSize
    global exporter
    global input_params

    if is_flow_slicer:
        my_online_streamer = NFStreamer(source=source,
                                        udps=FlowSlicer(limit=7))
    else:
        my_online_streamer = NFStreamer(source=source)

    counter = 0
    for flow in my_online_streamer:
        if int(flow.ip_version) == 6:
            continue
        counter += 1
        del flow.ip_version
        del flow.vlan_id
        del flow.src_ip_is_private
        del flow.dst_ip_is_private
        del flow.expiration_id
        del flow.application_name
        del flow.client_fingerprint
        del flow.server_fingerprint
        del flow.requested_server_name
        del flow.http_content_type
        del flow.application_category_name
        del flow.http_user_agent
        del flow.application_is_guessed

        # adding the flow to the first buffer
        bufferArray[0].append(flow)
        originalBufferSize += 1
        loop(counter=counter)

    while True:
        counter += 1
        loop(counter=counter)


def loop(counter) -> None:
    """
    Loop function for the capture process. It will call the step function, then it will update the exporter if it is
    enabled. After that, it will sleep for the aggregation frequency.

    :param counter: counter for the loop (maximum number of steps)
    :return: None
    """
    tstart = datetime.now()

    step(counter=counter,
         T_d=float(input_params.T),
         sw=int(input_params.sw),
         ARU_CThresh=float(input_params.ARU_CThresh),
         dynamicThreshold=str(input_params.dynamicT),
         payloadC=str(input_params.payloadC),
         memoryComparison=str(input_params.memoryComparison))

    if int(args.exporterStep) != 0:
        exporter.update(bufferArray=bufferArray,
                        ARU_t0=ARU_t0,
                        TCh_t0=TCh_t0,
                        T=T)

    tend = datetime.now()
    delta_time = tend - tstart
    delta_time = delta_time.total_seconds()

    sleep(float(input_params.aggregationFrequency) / 1000 - delta_time
          if float(input_params.aggregationFrequency) / 1000 >= delta_time
          else 0)

    delta_after_sleep = datetime.now()
    # Elapsed time can be used to check the resource usage of the solution
    deflicit = delta_after_sleep - tstart


def generateBuffers(ls, mil, mal, a, con, advancedIPComparison, relativeMemorySize) -> None:
    """
    Generate the buffers based on the given parameters. It will create a buffer for each parameter in the buffer list.
    The first buffer will contain all the parameters, the second buffer will contain all the parameters except the first
    one, and so on. The last buffer will contain only the last parameter.

    :param ls: param list
    :param mil: minimum list
    :param mal: maximum list
    :param a: accumulate list
    :param con: concat list
    :param advancedIPComparison: True if advanced IP comparison should be used, False otherwise
    :param relativeMemorySize: relative memory size
    :return: None
    """
    global bufferArray

    bufferArray.append(buffer.Buffer(id=0,
                                     fiveTuple=ls,
                                     params=None,
                                     mil=mil,
                                     mal=mal,
                                     a=a,
                                     con=con,
                                     advancedIPComparison=advancedIPComparison))
    for i in range(1, len(ls) + 1, 1):
        bufferArray.append(buffer.Buffer(id=i,
                                         fiveTuple=ls[i:],
                                         params=ls[i - 1:i],
                                         mil=mil,
                                         mal=mal,
                                         a=a,
                                         con=con,
                                         advancedIPComparison=advancedIPComparison))
    bufferArray[0].set_relative_memory_size(relativeMemorySize)


def printBuffers() -> None:
    """
    Print the flows in the buffers.

    :return: None
    """
    global bufferArray

    for b in bufferArray:
        b.getFlows()


def slideWindow(sw) -> None:
    """
    Slide the window. It will pop the first element from the ARU array if the size of the ARU array is equal to the
    sliding window.

    :param sw: sliding window
    :return: None
    """
    global ARU

    if int(sw) == -1:
        return

    if len(ARU) == int(sw):
        ARU.pop(0)


def get_flow_count() -> int:
    """
    Count the number of flows in the buffer arrays. It will loop through all the buffers and sum the number of flows.

    :return: number of flows in the buffer arrays
    """
    global bufferArray
    __count = 0
    for __buffer in bufferArray:
        __count += len(__buffer.bufferedArray)
    return __count


def calcARU(memoryComparison, sw: int = -1, ARU_CThresh: int = 98) -> None:
    """
    Calculate the ARU value. It will calculate the CPU usage, then it will calculate the sigma value based on the
    memoryComparison parameter. If the memoryComparison parameter is True, then the sigma value will be calculated
    based on the flow count and the relative memory size of the first buffer. If the memoryComparison parameter is
    False, then the sigma value will be calculated based on the CPU usage. If the memoryComparison parameter is not
    True or False, then the sigma value will be calculated based on the CPU usage and the memory usage of the python
    script. After that, it will slide the window and append the sigma value to the ARU array. After that, it will
    calculate the TCh value based on the ARU value and the ARU critical threshold. After that, it will slide the
    window and append the TCh value to the TCh array.

    :param memoryComparison: memory comparison mode
    :param sw: sliding window
    :param ARU_CThresh: ARU critical threshold
    :return: None
    """
    global ARU
    global ARU_t0
    global ARU_t1
    global TCh_t0
    global TCh_t1
    global bufferArray

    cpu_usage = 0.0
    __counter = 0
    while cpu_usage == 0.0:
        if __counter == 10:
            if len(ARU) > 0:
                cpu_usage = ARU[-1]
                break
            else:
                __counter = 0
        cpu_usage = cpu_percent(interval=0.001)
        __counter += 1

    if str(memoryComparison) == 'True':
        sigma = round((get_flow_count() / bufferArray[0].get_relative_memory_size() + cpu_usage) / 2, 4)
    elif str(memoryComparison) == 'False':
        sigma = round(cpu_usage, 4)
    else:
        sigma = round((cpu_usage + Process(getpid()).memory_percent()) / 2, 4)

    slideWindow(sw=sw)
    ARU.append(sigma)

    TCH_temp = 0
    ARU_temp = 0
    _temp = 0
    for element in ARU:
        _temp += element

    ARU_value = _temp / len(ARU)

    if 1.0 <= ARU_value <= float(ARU_CThresh):
        TCH_temp = 0
    elif float(ARU_CThresh) < ARU_value <= 100.0:
        TCH_temp = 1
    else:
        TCh_temp = 0  # -1

    TCh_t0 = TCh_t1
    TCh_t1 = TCH_temp

    ARU_t0 = ARU_t1
    ARU_t1 = ARU_value


def getARUInformation() -> str:
    """
    Returns the ARU information as a string.

    :return: string of ARU information
    """
    global ARU_t0
    global ARU_t1

    if (ARU_t0 and ARU_t1) is not None:
        return " ARU_t0: " + str(round(ARU_t0, 4)) + "%, ARU_t1: " + str(round(ARU_t1, 4)) + "%"
    else:
        return " ARU_t1: " + str(round(ARU_t1, 4)) + "%"


def getTChInformation() -> str:
    """
    Returns the TCh information as a string.

    :return: string of THc information
    """
    global TCh_t0
    global TCh_t1

    if (TCh_t0 and TCh_t1) is not None:
        return f'TCH_t0: {round(TCh_t0, 4)}, TCh_t1: {round(TCh_t1, 4)}'
    else:
        return f'TCH_t1: {round(TCh_t1, 4)}'


def adjustThreshold(T_d, dynamicThreshold="False") -> None:
    """
    Adjust the threshold based on the ARU and TCh values. If the dynamic thresholding is enabled, then the threshold
    will be adjusted based on the T_d and the ARU values. If the dynamic thresholding is disabled, then the threshold
    will be adjusted based on the T_d and the TCh values.

    :param T_d: default threshold
    :param dynamicThreshold: dynamic thresholding
    :return: None
    """
    global TCh_t0
    global TCh_t1
    global ARU_t0
    global ARU_t1
    global T

    if str(dynamicThreshold) == "False":
        T_var = T_d
    elif T is None and str(dynamicThreshold) == "True":
        T_var = T_d
    else:
        T_var = T

    if TCh_t0 == 1 or TCh_t1 == 1:
        if TCh_t0 < TCh_t1:
            T = 2.0 * T_d
        else:
            T = T_d / 2.0
    else:
        if TCh_t0 < TCh_t1:
            if T is None:
                T = (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var
            else:
                T = T + (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var

        else:
            if T is None:
                T = (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var
            else:
                T = (T - (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var) if (T - (
                    abs(ARU_t0 - ARU_t1)) / 100.0 * T_var) > 0 else 0


def moveEntry(i) -> None:
    """
    Move the last element from the buffer array i to the buffer array i+1. It will delete the last element from the
    buffer array i.

    :param i: index of the buffer array
    :return: None
    """
    # az adott NFEntry elmozgatasa B_{n}-bol B_{n+1}-be
    global bufferArray

    lastEntry = bufferArray[i].lastElement()
    bufferArray[i + 1].append(lastEntry)
    bufferArray[i].delete(lastEntry)


def step__init__(sw, ARU_CThresh, T_d, dynamicThreshold, memoryComparison) -> None:
    """
    Initialize the step function. It will calculate the ARU and TCh values, then it will adjust the threshold. If the
    first init is not done for ARU then the captures will be misled. That is why the init is done twice.

    :param sw: sliding window
    :param ARU_CThresh: ARU critical threshold
    :param T_d: default threshold
    :param dynamicThreshold: dynamic thresholding
    :param memoryComparison: memory comparison mode
    :return: None
    """
    global T

    calcARU(sw=sw, ARU_CThresh=ARU_CThresh, memoryComparison=memoryComparison)
    calcARU(sw=sw, ARU_CThresh=ARU_CThresh, memoryComparison=memoryComparison)

    adjustThreshold(T_d, dynamicThreshold=dynamicThreshold)


def flow_count() -> int:
    """
    Count the number of flows in the buffer arrays. It will loop through all the buffers and sum the number of flows.

    :return: number of flows in the buffer arrays
    """
    global bufferArray

    __count = 0
    for __buffer in bufferArray:
        __count += len(__buffer.bufferedArray)
    return __count


def step(counter, T_d, sw, ARU_CThresh, dynamicThreshold, memoryComparison, payloadC="False") -> None:
    """
    Step function for the solution. It will calculate the ARU and TCh values, then it will adjust the threshold. After
    that, it will loop through the buffer arrays and check if the last element is smaller than the threshold. If it is
    smaller, then it will move the last element to the next buffer array. If the last element is bigger than the
    threshold, then it will break the loop. If the last element is bigger than the threshold, then it will check if the
    buffer array is full. If it is full, then it will move the last element to the next buffer array. If the buffer
    array is not full, then it will break the loop.

    :param counter: counter for the loop (maximum number of steps)
    :param T_d: default threshold
    :param sw: sliding window
    :param ARU_CThresh: ARU critical threshold
    :param dynamicThreshold: dynamic thresholding
    :param memoryComparison: memory comparison mode
    :param payloadC: payload comparison
    :return: None
    """
    global bufferArray
    global entries
    global T
    global originalBufferSize

    calcARU(sw=sw, ARU_CThresh=ARU_CThresh, memoryComparison=memoryComparison)
    adjustThreshold(T_d, dynamicThreshold=dynamicThreshold)

    for i in range(0, len(bufferArray) - 1, 1):
        if str(payloadC) == "False":
            if bufferArray[i].lastElement() is not False and bufferArray[i].payload() < T:
                moveEntry(i)
                break
        else:
            if bufferArray[i].lastElement() is not False and bufferArray[i].payload() > T:
                moveEntry(i)
                break

        if bufferArray[i].lastElement() is not False and int(bufferArray[0].get_relative_memory_size()) <= int(
                flow_count()):
            moveEntry(i)


def main(input_params) -> None:
    """
    Main function of the solution. It will initialize the buffers, then it will start the capture process.

    :param input_params: Param list from argument parser or default.ini file
    :return: None
    """
    global bufferArray
    global ARU_t0
    global TCh_t0
    global T
    global exporter

    generateBuffers(ls=input_params.paramList,
                    mil=input_params.minimumList,
                    mal=input_params.maximumList,
                    a=input_params.accumulateList,
                    con=input_params.concatList,
                    advancedIPComparison=input_params.advancedIPC,
                    relativeMemorySize=input_params.relativeMemorySize)

    step__init__(sw=int(input_params.sw),
                 ARU_CThresh=float(input_params.ARU_CThresh),
                 dynamicThreshold=str(input_params.dynamicT),
                 T_d=float(input_params.T),
                 memoryComparison=str(input_params.memoryComparison))

    # exporter controller initializations
    if int(args.exporterStep) != 0:
        exporter = plt_graphics.ExporterController(bufferArray=bufferArray,
                                                   tick=args.exporterStep,
                                                   ARU_t0=ARU_t0,
                                                   TCh_t0=TCh_t0,
                                                   graphLength=args.graphLength,
                                                   graphWidth=args.exportedGraphWidth,
                                                   grapHeight=args.exportedGrapHeight,
                                                   fieldNames=args.concatList + args.paramList + args.minimumList + args.maximumList + args.accumulateList,
                                                   T=T)

    capture(dl=input_params.dropList, source=args.source)


def argparserPrint(args) -> None:
    """
    Print the command line arguments.

    :param args: command line arguments
    :return: None
    """
    print("Source: " + ''.join(args.source))
    print("Threshold: " + ''.join(args.T))
    print("Sliding window: " + ''.join(args.sw))
    print("BufferList: " + ','.join(args.paramList))
    print("MinimumList: " + ','.join(args.minimumList))
    print("MaximumList: " + ','.join(args.maximumList))
    print("AccumulateList: " + ','.join(args.accumulateList))
    print("ConcatList: " + ','.join(args.concatList))
    print("DropList: " + ','.join(args.dropList))
    print("Dynamic Threshold: " + ''.join(args.dynamicT))
    print("Payload comparison: " + ''.join(args.payloadC))
    print("Advanced IP comparison: " + ''.join(args.advancedIPC))
    print("Memory comparison mode: " + ''.join(args.memoryComparison))
    print("ARU critical threshold value: " + ''.join(args.ARU_CThresh))
    print("Exporter step time for data generation : " + ''.join(args.exporterStep))
    print("Exporter graps x-axis length: " + ''.join(args.graphLength))
    print("Aggregation frequency: " + ''.join(args.aggregationFrequency))
    print("Exporter width: " + ''.join(args.exportedGraphWidth))
    print("Exporter height: " + ''.join(args.exportedGrapHeight))
    print('Relative memory size {}'.format(args.relativeMemorySize))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Adaptive Gradual Flow Aggregation Demo Tool')

    # adding arguments
    parser.add_argument('-i', '--initialize', help='Use default.ini file for config. {True/False}', dest='init')
    parser.add_argument('-sc', '--source', help='Set the capture source ethernet interface/pcap file. {String}',
                        dest='source')
    parser.add_argument('-t', '--threshold', help='Set default Threshold value. {Float}', dest='T')
    parser.add_argument('-s', '--sliding', help='Set default value for sliding window. {Integer}', dest='sw')
    parser.add_argument('-b', '-buffer', help='Set buffer parameter concentration list of fields. {String array}',
                        dest='paramList', nargs='+', type=str)
    parser.add_argument('-mi', '--min', help='Merge columns by minimum value of fields. {String array}',
                        dest='minimumList', nargs='+', type=str)
    parser.add_argument('-ma', '--max', help='Merge columns by maximum value of fields. {String array}',
                        dest='maximumList', nargs='+', type=str)
    parser.add_argument('-a', '-accumulate', help='Accumulate columns by fields. {String array}', dest='accumulateList',
                        nargs='+', type=str)
    parser.add_argument('-c', '--concat', help="Concat columns. {String array}", dest='concatList', nargs='+', type=str)
    parser.add_argument('-d', '-drop', help='Drop fields. {String array}', dest='dropList', nargs='+', type=str)
    parser.add_argument('-dt', '--dynamicThreshold', help='Enable dynamic thresholding. {True/False}', dest='dynamicT')
    parser.add_argument('-pc', '--payloadComparison', help='Switch payload comparison. {True/False}', dest='payloadC')
    parser.add_argument('-aipc', '--advancedIPComparison', help='Switch to advanced IP comparison. {True/False}',
                        dest='advancedIPC')
    parser.add_argument('-mc', '--memoryC',
                        help='Switch memory comparison mode. True for all process memory total. False for just the python script usage of total. {True/False}',
                        dest='memoryComparison')
    parser.add_argument('-act', '--ARUCriticalThreshold', help='Set ARU critical value for thresholding. {Float}',
                        dest='ARU_CThresh')
    parser.add_argument('-e', '--exporterStep',
                        help='Set exporter step time for generate data. Set-up to 0 if you want to turn it off. {Integer}',
                        dest='exporterStep')
    parser.add_argument('-al', '--graphLength', help='Set graphs x-axis length for visualize data. {Integer}',
                        dest='graphLength')
    parser.add_argument('-f', '--aggregationFrequency', help='Set aggregation frequency (ms). {Float}',
                        dest='aggregationFrequency')
    parser.add_argument('-w', '--width', help="Set exporter graphs width (pixel). {Integer}", dest='exportedGraphWidth')
    parser.add_argument('-hi', '--height', help="Set exporter graphs height (pixel). {Integer}",
                        dest='exportedGrapHeight')
    parser.add_argument('-rms', '--relativememorysize', help='Set the relative memory size (packet count). {Integer}',
                        dest='relativeMemorySize')

    args = parser.parse_args()

    if str(args.init) == str(False):
        # starting the solution using the command line parameters
        argparserPrint(args)
        main(args)

    else:
        # if the default config file is set to true, then it will be preloaded based on the default.ini file
        config = configparser.ConfigParser()
        if not path.isfile(path.join(dirname, 'default.ini')):
            print("ERROR (002): default config file is missing! Please use console configuration!")

        config.read(path.join(dirname, 'default.ini'))

        args.source = config['DEFAULT']['source']
        args.T = config['DEFAULT']['threshold']
        args.sw = config['DEFAULT']['slidingWindow']
        args.paramList = ast.literal_eval(config['DEFAULT']['bufferList'])
        args.minimumList = ast.literal_eval(config['DEFAULT']['minimumList'])
        args.maximumList = ast.literal_eval(config['DEFAULT']['maximumList'])
        args.accumulateList = ast.literal_eval(config['DEFAULT']['accumulateList'])
        args.dropList = ast.literal_eval(config['DEFAULT']['dropList'])
        args.dynamicT = config['DEFAULT']['dynamicThreshold']
        args.payloadC = config['DEFAULT']['payloadComparsion']
        args.advancedIPC = config['DEFAULT']['advancedIPComparison']
        args.ARU_CThresh = config['DEFAULT']['ARUCThresh']
        args.exporterStep = config['DEFAULT']['exporterStep']
        args.graphLength = config['DEFAULT']['graphLength']
        args.aggregationFrequency = config['DEFAULT']['aggregationFrequency']
        args.exportedGraphWidth = config['DEFAULT']['exportedGraphWidth']
        args.concatList = ast.literal_eval(config['DEFAULT']['concatList'])
        args.exportedGrapHeight = config['DEFAULT']['exportedGrapHeight']
        args.memoryComparison = config['DEFAULT']['memoryComparison']
        args.relativeMemorySize = config['DEFAULT']['relativeMemorySize']

        argparserPrint(args)

        input_params = args
        main(args)
