from nfstream import NFStreamer, NFPlugin
from pympler import asizeof
from psutil import cpu_percent, virtual_memory, Process
import argparse
from os import path, getpid
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
(TCh_t0,TCh_t1) = (None,None)
(ARU_t0,ARU_t1) = (None,None)
T = None
originalBufferSize = 0
(input_params,exporter) = (None,None)

'''
# NFPlugin hogy a flow expariton.id-ket -1re pakoljuk, ne legyenek aggregalva
class FlowSlicer(NFPlugin):
    counter = 1

    def on_init(self, packet, flow):
        if self.limit == 1:
            flow.expiration_id = -1

    def on_update(self, packet, flow):
        if self.limit == flow.bidirectional_packets:
            flow.expiration_id = -1
'''

def capture(dl,source):
    global bufferArray
    global originalBufferSize
    global exporter
    global input_params

    my_online_streamer = NFStreamer(source=source)#,
                                    #udps=FlowSlicer(limit=7))
    counter = 0
    for flow in my_online_streamer:
        if int(flow.ip_version) == 6:
            continue
        counter += 1
        # ki kell a drop listes elemeket dobalni
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

        '''
        for param in dl:
            delattr(flow,param)
        '''

        # 0-as deffault bufferbe pakolunk mindent
        bufferArray[0].append(flow)
        originalBufferSize += 1

        # print("Incomming traffic: " + str(flow.id))
        loop(counter=counter)

    while True:
        counter += 1
        loop(counter=counter)


def loop(counter):
    # tstart & tend azert kell hogg tudjuk merni az eltelt idot
    tstart = datetime.now()

    # ez lesz a forgo algoritmus ami dolgozik tovabb
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
    deflicit = delta_after_sleep - tstart
    #print(f"Elasped time: {deflicit}")


def generateBuffers(ls, mil, mal, a, con, advancedIPComparison, relativeMemorySize):
    global bufferArray

    bufferArray.append(buffer.Buffer(id=0,
                                     fiveTuple=ls,
                                     params=None,
                                     mil=mil,
                                     mal=mal,
                                     a=a,
                                     con=con,
                                     advancedIPComparison=advancedIPComparison))
    for i in range(1,len(ls)+1,1):
        bufferArray.append(buffer.Buffer(id=i,
                                         fiveTuple=ls[i:],
                                         params=ls[i-1:i],
                                         mil=mil,
                                         mal=mal,
                                         a=a,
                                         con=con,
                                         advancedIPComparison=advancedIPComparison))
    bufferArray[0].set_relative_memory_size(relativeMemorySize)


def printBuffers():
    global bufferArray

    # az egyes bufferekben a flowok kiprintelese
    # NFEntry-k listazasa az adott bufferekben
    for b in bufferArray:
        b.getFlows()


def slideWindow(sw):
    global ARU

    # defualtban sw=-1 ekkor unlimited lepes van ezt is cskekolni kell
    if int(sw) == -1:
        return

    # annyi fog tortenni hogy ha ARU merete == sw-vel akkor pop-oljuk az elso elemet
    if len(ARU) == int(sw):
        ARU.pop(0)


def get_flow_count():
    global bufferArray
    __count = 0
    for __buffer in bufferArray:
        __count += len(__buffer.bufferedArray)
    return __count
    #return len(bufferArray[0].bufferedArray)


def calcARU(memoryComparison,sw=-1,ARU_CThresh=98):
    global ARU
    global ARU_t0
    global ARU_t1
    global TCh_t0
    global TCh_t1
    global bufferArray

    # kiszamoljuk a kezdo %-okat
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
        sigma = round((get_flow_count()/bufferArray[0].get_relative_memory_size() + cpu_usage)/2,4)
        #sigma = round((cpu_usage + virtual_memory().percent)/2,4)
    elif str(memoryComparison) == 'False':
        sigma = round(cpu_usage,4)
    else:
        sigma = round((cpu_usage + Process(getpid()).memory_percent())/2,4)
    #sigma = (cpu_percent(interval=1) + Process(getpid()).memory_percent()) / 2
    #sigma = round(sigma, 4)

    # mielott uj elem kerulne bele toljuk a windowot
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
        #print("ERROR (001): ARU_value: " + str(ARU_value) + " . Setting TCh_temp to 1.0!")
        TCh_temp = 0#-1

    TCh_t0 = TCh_t1
    TCh_t1 = TCH_temp

    ARU_t0 = ARU_t1
    ARU_t1 = ARU_value


def getARUInformation():
    global ARU_t0
    global ARU_t1

    if (ARU_t0 and ARU_t1) is not None:
        return " ARU_t0: " + str(round(ARU_t0, 4)) + "%, ARU_t1: " + str(round(ARU_t1, 4)) + "%"
    else:
        return " ARU_t1: " + str(round(ARU_t1, 4)) + "%"


def getTChInformation():
    global TCh_t0
    global TCh_t1

    if ( TCh_t0 and TCh_t1 ) is not None:
        return f'TCH_t0: {round(TCh_t0,4)}, TCh_t1: {round(TCh_t1,4)}'
    else:
        return f'TCH_t1: {round(TCh_t1,4)}'


def adjustThreshold(T_d, dynamicThreshold="False"):
    global TCh_t0
    global TCh_t1
    global ARU_t0
    global ARU_t1
    global T
    # adjustolni kell a thresholdot a THc fuggvenyeben
    # T_d a default threshold

    # dinamikus threshold beallitaas itt tortenik defaultkent False
    if str(dynamicThreshold) == "False":
        T_var = T_d
    elif T is None and str(dynamicThreshold) == "True":
        T_var = T_d
    else:
        T_var = T

    # ezek utan pedig meg kell vizsgalni benne van e a kritikusban
    # 0 eseten nem kritikus
    # 1 eseten pedig kritikus
    if TCh_t0 == 1 or TCh_t1 == 1:
        if TCh_t0 < TCh_t1:
            T = 2.0 * T_d
        else:
            T = T_d / 2.0
    else:
        if TCh_t0 < TCh_t1:
            # elso korben None kent fog szerepelni a T erteke ezert ebben az esetben
            # modositas mentes agnak kell lefutnia
            if T is None:
                T = (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var
            else:
                T = T + (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var

        else:
            if T is None:
                T = (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var
            else:
                T = (T - (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var) if (T - (abs(ARU_t0 - ARU_t1)) / 100.0 * T_var) > 0 else 0


def moveEntry(i):
    # az adott NFEntry elmozgatasa B_{n}-bol B_{n+1}-be
    global bufferArray

    # megnezzuk van-e elemenet a B_{n} bufferban
    # ha van akkor attesszuk a B_{n+1}-be es kitoroljuk az entryt a B_{n}-bol
    lastEntry = bufferArray[i].lastElement()
    bufferArray[i + 1].append(lastEntry)
    bufferArray[i].delete(lastEntry)


def step__init__(sw, ARU_CThresh, T_d, dynamicThreshold, memoryComparison):
    global T

    calcARU(sw=sw,ARU_CThresh=ARU_CThresh,memoryComparison=memoryComparison)
    calcARU(sw=sw,ARU_CThresh=ARU_CThresh,memoryComparison=memoryComparison)

    # ezek utan meg adaptalni kell!
    adjustThreshold(T_d, dynamicThreshold=dynamicThreshold)

    #print("Step: 0. Total sum size of buffers: " + str(
    #    asizeof.asizeof(bufferArray)) + " bytes." + getARUInformation() + getTChInformation())
    #printBuffers()


def flow_count():
    global bufferArray

    __count = 0
    for __buffer in bufferArray:
        __count += len(__buffer.bufferedArray)
    return __count


def step(counter,T_d, sw, ARU_CThresh, dynamicThreshold, memoryComparison, payloadC="False"):
    global bufferArray
    global entries
    global T
    global originalBufferSize
    '''
    # minden kor elejen kirjuk a dolgokat
    print("Step: " + str(counter) +
          ". Total sum size of buffers: " + str(asizeof.asizeof(bufferArray)) +
          " bytes." + getARUInformation() + getTChInformation() +
          ", T value: " + str(round(float(T),4)) +
          ", Entries compression rate: " + str((round((1 - (len(bufferArray[0].bufferedArray) / originalBufferSize +
                                                         len(bufferArray[1].bufferedArray) / originalBufferSize +
                                                         len(bufferArray[2].bufferedArray) / originalBufferSize +
                                                         len(bufferArray[3].bufferedArray) / originalBufferSize +
                                                         len(bufferArray[4].bufferedArray) / originalBufferSize +
                                                         len(bufferArray[5].bufferedArray) / originalBufferSize)) * 100 ,4)) if originalBufferSize > 0 else 0.0) + "%")
    '''
    # T adaptalasa
    # eloszor ki kell szamolni AUR-t meg a TCh-t
    calcARU(sw=sw, ARU_CThresh=ARU_CThresh,memoryComparison=memoryComparison)

    # ezek utan meg adaptalni kell!
    adjustThreshold(T_d, dynamicThreshold=dynamicThreshold)

    '''
    for i in range(0,len(bufferArray)-1,1):
        if bufferArray[i].lastElement() is not False and int(bufferArray[0].get_relative_memory_size()) <= int(flow_count()):
            moveEntry(i)
    '''

    # vegig megyunk az osszes bufferarray-en minden korben megnezzuk hogy az octetcount
    # nagyobb-e mint T es ha nagyobb attesszuk
    for i in range(0,len(bufferArray)-1,1):
        if str(payloadC) == "False":
            if bufferArray[i].lastElement() is not False and bufferArray[i].payload() < T:
                moveEntry(i)
                break
        else:
            if bufferArray[i].lastElement() is not False and bufferArray[i].payload() > T:
                moveEntry(i)
                break

        if bufferArray[i].lastElement() is not False and int(bufferArray[0].get_relative_memory_size()) <= int(flow_count()):
            moveEntry(i)
        '''
        if i == 0 and bufferArray[i].lastElement() is not False and int(bufferArray[0].get_relative_memory_size()) <= int(flow_count()):
            moveEntry(i)
        '''


def main(input_params):
    global bufferArray
    global ARU_t0
    global TCh_t0
    global T
    global exporter

    # bufferek legeneralasa kell amit a buffer osztalybol kell peldanyositani bementi szamszor
    generateBuffers(ls=input_params.paramList,
                    mil=input_params.minimumList,
                    mal=input_params.maximumList,
                    a=input_params.accumulateList,
                    con=input_params.concatList,
                    advancedIPComparison=input_params.advancedIPC,
                    relativeMemorySize=input_params.relativeMemorySize)

    # fel kell tolteni a default step-et
    step__init__(sw=int(input_params.sw),
                 ARU_CThresh=float(input_params.ARU_CThresh),
                 dynamicThreshold=str(input_params.dynamicT),
                 T_d=float(input_params.T),
                 memoryComparison=str(input_params.memoryComparison))

    # exportet controller inicializalasa
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

    # teszt buildhez eloszor kiszedjuk most kulon tombbe az adatokat a jobb atlathatosag miatt!
    capture(dl=input_params.dropList,source=args.source)


def argparserPrint(args):
    # argparserben szereplo ertekek kiprinteleshez van
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
    parser = argparse.ArgumentParser(description='Network Buffering Tool v2.0')

    # itt jonnek az argumentumok
    parser.add_argument('-i', '--initialize', help='Use default.ini file for config. {True/False}', dest='init')
    parser.add_argument('-sc', '--source', help='Set the capture source ethernet interface/pcap file. {String}', dest='source')
    parser.add_argument('-t', '--threshold',help='Set default Threshold value. {Float}', dest='T')
    parser.add_argument('-s', '--sliding', help='Set default value for sliding window. {Integer}', dest='sw')
    parser.add_argument('-b', '-buffer',help='Set buffer parameter concentration list of fields. {String array}', dest='paramList', nargs='+', type=str)
    parser.add_argument('-mi', '--min', help='Merge columns by minimum value of fields. {String array}', dest='minimumList', nargs='+', type=str)
    parser.add_argument('-ma', '--max', help='Merge columns by maximum value of fields. {String array}', dest='maximumList', nargs='+', type=str)
    parser.add_argument('-a', '-accumulate', help='Accumulate columns by fields. {String array}', dest='accumulateList', nargs='+', type=str)
    parser.add_argument('-c', '--concat', help="Concat columns. {String array}", dest='concatList', nargs='+', type=str)
    parser.add_argument('-d', '-drop', help='Drop fields. {String array}', dest='dropList', nargs='+', type=str)
    parser.add_argument('-dt', '--dynamicThreshold', help='Enable dynamic thresholding. {True/False}', dest='dynamicT')
    parser.add_argument('-pc', '--payloadComparison', help='Switch payload comparison. {True/False}', dest='payloadC')
    parser.add_argument('-aipc', '--advancedIPComparison', help='Switch to advanced IP comparison. {True/False}', dest='advancedIPC')
    parser.add_argument('-mc', '--memoryC', help='Switch memory comparison mode. True for all process memory total. False for just the python script usage of total. {True/False}',dest='memoryComparison')
    parser.add_argument('-act', '--ARUCriticalThreshold', help='Set ARU critical value for thresholding. {Float}', dest='ARU_CThresh')
    parser.add_argument('-e', '--exporterStep', help='Set exporter step time for generate data. Set-up to 0 if you want to turn it off. {Integer}',dest='exporterStep')
    parser.add_argument('-al', '--graphLength', help='Set graphs x-axis length for visualize data. {Integer}', dest='graphLength')
    parser.add_argument('-f','--aggregationFrequency', help='Set aggregation frequency (ms). {Float}', dest='aggregationFrequency')
    parser.add_argument('-w','--width', help="Set exporter graphs width (pixel). {Integer}",dest='exportedGraphWidth')
    parser.add_argument('-hi','--height', help="Set exporter graphs height (pixel). {Integer}", dest='exportedGrapHeight')
    parser.add_argument('-rms', '--relativememorysize', help='Set the relative memory size (packet count). {Integer}', dest='relativeMemorySize')

    args = parser.parse_args()

    if str(args.init) == str(False):
        # bemeneteli parameterekkel tortenik az inditas
        argparserPrint(args)
        main(args)

    else:
        # ha truet kapott a beolvasasra akkor a default.ini fajl alapjan tortenik az elinditas!
        config = configparser.ConfigParser()
        if not path.isfile(path.join(dirname, 'default.ini')):
            print("ERROR (002): default config file is missing! Please use console configuration!")

        config.read(path.join(dirname,'default.ini'))

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

    # test case ha az argparsert hasznaljuk nem a default.ini fajlt
    #python3 main.py -t 100000 -s 10 -b protocol src_port dst_port src_ip dst_ip  -mi bidirectional_first_seen_ms src2dst_first_seen_ms dst2src_first_seen_ms -ma bidirectional_last_seen_ms src2dst_last_seen_ms dst2src_last_seen_ms -a bidirectional_packets bidirectional_raw_bytes bidirectional_ip_bytes bidirectional_duration_ms src2dst_packets src2dst_raw_bytes src2dst_ip_bytes src2dst_duration_ms dst2src_packets dst2src_raw_bytes dst2src_ip_bytes dst2src_duration_ms -d id version vlan_id src_ip_type dst_ip_type expiration_id -dt False -pc False -aipc False -act 98
