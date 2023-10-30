from pympler.asizeof import asizeof
import advanced_matching


class Buffer:
    __relativeMemorySize = 0

    def __init__(self, id, fiveTuple, params, mil, mal, a, con, advancedIPComparison):
        self.id = id
        self.bufferedArray = []

        '''
        # TODO FIVE TUPLE
        self._protocol = _protocol
        self._src_port = _src_port
        self._dst_port = _dst_port
        self._src_ip = _src_ip
        self._dst_ip = _dst_ip
        '''

        # ez lesz a fontossagi sorrend tombkent kapja meg []
        self.params = params
        self.fiveTuple = fiveTuple
        self.mil = mil
        self.mal = mal
        self.a = a
        self.con = con
        self.advancedIPComparison = advancedIPComparison

        # abban az esetben ha advanced be van kapcsolva leztre kell hozni a rootot a luleahoz
        if str(advancedIPComparison) == "True":
            # root src es dst lesz letrehozasa ebben az esetben
            self.root_src = advanced_matching.Lulea_node('*')
            self.root_dst = advanced_matching.Lulea_node('*')

    def set_relative_memory_size(self, relativeMemorySize: int) -> None:
        """
        # TODO make this function description
        Ez a funkció beállitja a relativ memória méretet, ezt származtatni kell a ténylegesből mert nincs memória
        menedzsment a pythonban olyan ami a P4 esetén előáll.

        :rtype
        :param relativeMemorySize:
        :return:
        """
        Buffer.__relativeMemorySize = relativeMemorySize

    def get_relative_memory_size(self) -> int:
        """
        # TODO kiegésziteni
        :rtype int
        :return:
        """
        return int(Buffer.__relativeMemorySize)

    def containsEntry(self, other):
        # ez annak kell lennie hogy a bufferedArray-ben van-e adott elemetn ha van hozza kell adni amugy kidobni
        # itt majd kell valami binaris / hash megvalositasos trukk!
        times = 0
        for i in self.bufferedArray:
            for j in self.fiveTuple:
                # megnezzuk ha megegyezik ket attributum akkor tovabb megyunk
                # itt meg kell csinalni hogy ha az attributum neve a "src_ip","dst_ip" akkor csak ezeket
                # hasonlista ossze a lulea algoritmussal
                skip = False

                if self.advancedIPComparison == "True":
                    if str(j) == "src_ip":
                        val = advanced_matching.find_prefix(root=self.root_src,
                                                            prefix=advanced_matching.pre_process_ip_addr(other.src_ip))
                                                            #prefix=advanced_matching.pre_process_ip_addr(getattr(other,j)))
                        if val[0]:
                            times += 1
                            skip = True

                    elif str(j) == "dst_ip":
                        val = advanced_matching.find_prefix(root=self.root_dst,
                                                            prefix=advanced_matching.pre_process_ip_addr(other.dst_ip))
                                                            #prefix=advanced_matching.pre_process_ip_addr(getattr(other,j)))
                        if val[0]:
                            times += 1
                            skip = True

                if not skip and getattr(i,j) == getattr(other,j):
                    times += 1

            if times == len(self.fiveTuple):
                return i
            else:
                times = 0
        return False

    def smallest_bidirectional_bytes(self):
        smallest = self.bufferedArray[0]
        for element in self.bufferedArray:
            if element.bidirectional_bytes < smallest.bidirectional_bytes:
                smallest = element
        return smallest

    def lastElement(self):
        if len(self.bufferedArray) == 0:
            return False
        else:
            return self.smallest_bidirectional_bytes()
            #return self.bufferedArray[-1]

    def concatElements(self,NFEntry_1, NFEntry_2):
        # FONTOS: NFEntry_1 mindig ami mar szerepel a tablaban
        # es NFEntry_2 id mezojet atteszuk NFEntry_1
        NFEntry_1.id = f'{NFEntry_1.id}:{NFEntry_2.id}'
        '''
        for param in self.con:
            firstPart = str(getattr(NFEntry_1,param))
            secondPart = str(getattr(NFEntry_2,param))
            setattr(NFEntry_1,param,firstPart + ':' + secondPart)
        '''

    def takeMinimum(self,NFEntry_1,NFEntry_2):
        # FONTOS: NFEntry_1 mindig ami mar szerepel a tablaban
        # es NFEntry_2 lesz az amit be akarunk tenni!
        if float(NFEntry_1.bidirectional_first_seen_ms) == float(0) or float(NFEntry_1.bidirectional_first_seen_ms) == float(-1):
            NFEntry_1.bidirectional_first_seen_ms = NFEntry_2.bidirectional_first_seen_ms
        elif float(NFEntry_2.bidirectional_first_seen_ms) < float(NFEntry_1.bidirectional_first_seen_ms):
            NFEntry_1.bidirectional_first_seen_ms = NFEntry_2.bidirectional_first_seen_ms

        if float(NFEntry_1.src2dst_first_seen_ms) == float(0) or float(NFEntry_1.src2dst_first_seen_ms) == float(-1):
            NFEntry_1.src2dst_first_seen_ms = NFEntry_2.src2dst_first_seen_ms
        elif float(NFEntry_2.src2dst_first_seen_ms) < float(NFEntry_1.src2dst_first_seen_ms):
            NFEntry_1.src2dst_first_seen_ms = NFEntry_2.src2dst_first_seen_ms

        if float(NFEntry_1.dst2src_first_seen_ms) == float(0) or float(NFEntry_1.dst2src_first_seen_ms) == float(-1):
            NFEntry_1.dst2src_first_seen_ms = NFEntry_2.dst2src_first_seen_ms
        elif float(NFEntry_2.dst2src_first_seen_ms) < float(NFEntry_1.dst2src_first_seen_ms):
            NFEntry_1.dst2src_first_seen_ms = NFEntry_2.dst2src_first_seen_ms
        '''
        for param in self.mil:
            if float(getattr(NFEntry_1,param)) == (float(0) or float(-1)):
                setattr(NFEntry_1,param,getattr(NFEntry_2,param))
            elif float(getattr(NFEntry_2,param)) < float(getattr(NFEntry_1,param)):
                setattr(NFEntry_1,param,getattr(NFEntry_2,param))
            else:
                continue
        '''

    def takeMaximum(self, NFEntry_1, NFEntry_2):
        # FONTOS: NFEntry_1 mindig ami mar szerepel a tablaban
        # es NFEntry_2 lesz az amit be akarunk tenni!
        if float(NFEntry_1.bidirectional_last_seen_ms) == float(0) or float(NFEntry_2.bidirectional_last_seen_ms) == float(-1):
            NFEntry_1.bidirectional_last_seen_ms = NFEntry_2.bidirectional_last_seen_ms
        elif float(NFEntry_1.bidirectional_last_seen_ms) < float(NFEntry_2.bidirectional_last_seen_ms):
            NFEntry_1.bidirectional_last_seen_ms = NFEntry_2.bidirectional_last_seen_ms

        if float(NFEntry_1.src2dst_last_seen_ms) == float(0) or float(NFEntry_2.src2dst_last_seen_ms) == float(-1):
            NFEntry_1.src2dst_last_seen_ms = NFEntry_2.src2dst_last_seen_ms
        elif float(NFEntry_1.src2dst_last_seen_ms) < float(NFEntry_2.src2dst_last_seen_ms):
            NFEntry_1.src2dst_last_seen_ms = NFEntry_2.src2dst_last_seen_ms

        if float(NFEntry_1.dst2src_last_seen_ms) == float(0) or float(NFEntry_2.dst2src_last_seen_ms) == float(-1):
            NFEntry_1.dst2src_last_seen_ms = NFEntry_2.dst2src_last_seen_ms
        elif float(NFEntry_1.dst2src_last_seen_ms) < float(NFEntry_2.dst2src_last_seen_ms):
            NFEntry_1.dst2src_last_seen_ms = NFEntry_2.dst2src_last_seen_ms
        '''
        for param in self.mal:
            if float(getattr(NFEntry_1,param)) == (float(0) or float(-1)):
                setattr(NFEntry_1,param,getattr(NFEntry_2,param))
            elif float(getattr(NFEntry_1,param)) < float(getattr(NFEntry_2,param)):
                setattr(NFEntry_1,param,getattr(NFEntry_2,param))
            else:
                continue
        '''

    def accumulate(self,NFEntry_1,NFEntry_2):
        # FONTOS: NFEntry_1 mindig ami mar szerepel a tablaban
        # es NFEntry_2 lesz az amit be akarunk tenni!
        NFEntry_1.bidirectional_packets = float(NFEntry_1.bidirectional_packets) + float(NFEntry_2.bidirectional_packets)
        NFEntry_1.bidirectional_bytes = float(NFEntry_1.bidirectional_bytes) + float(NFEntry_2.bidirectional_bytes)
        NFEntry_1.bidirectional_duration_ms = float(NFEntry_1.bidirectional_duration_ms) + float(NFEntry_2.bidirectional_duration_ms)
        NFEntry_1.src2dst_packets = float(NFEntry_1.src2dst_packets) + float(NFEntry_2.src2dst_packets)
        NFEntry_1.src2dst_duration_ms = float(NFEntry_1.src2dst_duration_ms) + float(NFEntry_2.src2dst_duration_ms)
        NFEntry_1.dst2src_packets = float(NFEntry_1.dst2src_packets) + float(NFEntry_2.dst2src_packets)
        NFEntry_1.dst2src_duration_ms = float(NFEntry_1.dst2src_duration_ms) + float(NFEntry_2.dst2src_duration_ms)
        NFEntry_1.src2dst_bytes = float(NFEntry_1.src2dst_bytes) + float(NFEntry_2.src2dst_bytes)
        NFEntry_1.dst2src_bytes = float(NFEntry_1.dst2src_bytes) + float(NFEntry_2.dst2src_bytes)
        '''
        for param in self.a:
            setattr(NFEntry_1,param,float(getattr(NFEntry_1,param))+float(getattr(NFEntry_2,param)))
        '''

    def append(self, NFEntry):
        if self.params is None:
            self.bufferedArray.append(NFEntry)
            return

        # ki kell torolni ami nem kell a parameter lista alapjan
        for element in self.params:
            # meg kell nezni hogy van e neki egyaltalan ilyen mezo erteke

            # if-else itt is kilett veve mert nem jol mukodott ha 0 volt az ertek!
            #if getattr(NFEntry,element):
            delattr(NFEntry,element)
            #else:
            #    continue

        # a kitorles utan meg kell nezni hogy van-e ilyen rekord es ha van aggregalni kell
        # amugy meg cska bekerul a memoriaba
        if Buffer.containsEntry(self, NFEntry):
            #[1]-ben van benne az NFEntry_1!
            # vegig kell menni a minimumon maxon es az osszeadason
            NFEntry_1 = Buffer.containsEntry(self, NFEntry)
            self.takeMinimum(NFEntry_1=NFEntry_1,NFEntry_2=NFEntry)
            self.takeMaximum(NFEntry_1=NFEntry_1,NFEntry_2=NFEntry)
            self.accumulate(NFEntry_1=NFEntry_1,NFEntry_2=NFEntry)
            self.concatElements(NFEntry_1=NFEntry_1,NFEntry_2=NFEntry)
        else:
            self.bufferedArray.append(NFEntry)

            # annyi kiegeszites kell ide ha advanced ip matching bent van hogy ilyenkor
            # a roothoz hozza kell adni az adott stringet
            # src ip cim hozzadas
            if self.advancedIPComparison == "True":
                if self.id not in [3,4,5]:
                    #advanced_matching.add(root=self.root_src,word=advanced_matching.pre_process_ip_addr(getattr(NFEntry,"src_ip")))
                    advanced_matching.add(root=self.root_src, word=advanced_matching.pre_process_ip_addr(NFEntry.src_ip))
                if self.id not in [4,5]:
                    #advanced_matching.add(root=self.root_dst,word=advanced_matching.pre_process_ip_addr(getattr(NFEntry,"dst_ip")))
                    advanced_matching.add(root=self.root_dst,word=advanced_matching.pre_process_ip_addr(NFEntry.dst_ip))


    def delete(self, NFEntry):
        # amikor athelyezunk elemet az egyikbol a masikbe
        # akkor az eredetibol torolni kell miutan megtortent az ujba az append

        # abban az esetben ha be van kapcsolva es egy nfeentryt removolunk akkor elotte ki kell torolni a
        # fakbol az adott ertekeket
        if self.advancedIPComparison == "True":
            if self.id not in [3,4,5]:
                advanced_matching.delete(root=self.root_src,word=advanced_matching.pre_process_ip_addr(NFEntry.src_ip))
                #advanced_matching.delete(root=self.root_src,word=advanced_matching.pre_process_ip_addr(getattr(NFEntry,"src_ip")))
            if self.id not in [4,5]:
                advanced_matching.delete(root=self.root_dst,word=advanced_matching.pre_process_ip_addr(NFEntry.dst_ip))
                #advanced_matching.delete(root=self.root_dst,word=advanced_matching.pre_process_ip_addr(getattr(NFEntry,"dst_ip")))

        #if Buffer.containsEntry(self, NFEntry):
        self.bufferedArray.remove(NFEntry)
        #else:
        #    pass

    def getInformation(self):
        outParams = ""
        for p in self.params:
            outParams += p + ","
        print(f'Buffer {self.id} following values dropped: {outParams}')

    def payload(self):
        return self.lastElement().bidirectional_bytes
        #return asizeof.asizeof(self.bufferedArray)

    def payloadInformation(self):
        print(f'Payload size in buffer {self.id} : {asizeof(self.bufferedArray)} bytes.')

    def getFlows(self):
        print(f'Buffer {self.id}')
        for flow in self.bufferedArray:
            print(flow)

    def getFlowData(self):
        return self.bufferedArray

    def moveable(self):
        if len(self.bufferedArray) >= 2:
            return True
        return False
