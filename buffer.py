from pympler.asizeof import asizeof
import advanced_matching


class Buffer:
    __relativeMemorySize = 0

    def __init__(self, id, fiveTuple, params, mil, mal, a, con, advancedIPComparison):
        self.id = id
        self.bufferedArray = []

        self.params = params
        self.fiveTuple = fiveTuple
        self.mil = mil
        self.mal = mal
        self.a = a
        self.con = con
        self.advancedIPComparison = advancedIPComparison

        # if the advanced IP comparison is set to true then Luela algorithm is used for efficiency.
        if str(advancedIPComparison) == "True":
            self.root_src = advanced_matching.Lulea_node('*')
            self.root_dst = advanced_matching.Lulea_node('*')

    def set_relative_memory_size(self, relativeMemorySize: int) -> None:
        """
        This function sets the relative memory size, this should be derived from the actual memory size because there
        is no memory management in python. The size will be the constraint of the given buffer.

        :param relativeMemorySize: size of relative memory to allocate for a given buffer
        :return: None
        """
        Buffer.__relativeMemorySize = relativeMemorySize

    def get_relative_memory_size(self) -> int:
        """
        This function returns the relative memory size of the buffer.

        :return: relative memory size of the buffer
        """
        return int(Buffer.__relativeMemorySize)

    def containsEntry(self, other):
        """
        This function checks if the given element is in the buffer or not. If the element is in the buffer then
        the function returns the element else it returns False.

        :param other: element that should be checked
        :return: union of bool and None
        """
        times = 0
        for i in self.bufferedArray:
            for j in self.fiveTuple:
                skip = False

                if self.advancedIPComparison == "True":
                    if str(j) == "src_ip":
                        val = advanced_matching.find_prefix(root=self.root_src,
                                                            prefix=advanced_matching.pre_process_ip_addr(other.src_ip))
                        if val[0]:
                            times += 1
                            skip = True

                    elif str(j) == "dst_ip":
                        val = advanced_matching.find_prefix(root=self.root_dst,
                                                            prefix=advanced_matching.pre_process_ip_addr(other.dst_ip))
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
        """
        This function returns the element with the smallest bidirectional bytes in the buffer.

        :return: NFEntry with the smallest bidirectional bytes
        """
        smallest = self.bufferedArray[0]
        for element in self.bufferedArray:
            if element.bidirectional_bytes < smallest.bidirectional_bytes:
                smallest = element
        return smallest

    def lastElement(self):
        """
        This function returns the last element of the buffer if the buffer is not empty else it returns False.

        :return: union of bool and integer
        """
        if len(self.bufferedArray) == 0:
            return False
        else:
            return self.smallest_bidirectional_bytes()

    def concatElements(self, NFEntry_1, NFEntry_2) -> None:
        """
        This function concatenates the id of the given NFEntries and sets the concatenated id to the first NFEntry.

        :param NFEntry_1: NFEntry that should be modified
        :param NFEntry_2: NFEntry that should be modified
        :return:
        """
        NFEntry_1.id = f'{NFEntry_1.id}:{NFEntry_2.id}'

    def takeMinimum(self, NFEntry_1, NFEntry_2) -> None:
        """
        This function takes the minimum value of the given parameters of the given NFEntries and sets the minimum

        :param NFEntry_1: NFEntry that should be modified
        :param NFEntry_2: NFEntry that should be modified
        :return: None
        """
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

    def takeMaximum(self, NFEntry_1, NFEntry_2) -> None:
        """
        This function takes the maximum value of the given parameters of the given NFEntries and sets the maximum

        :param NFEntry_1: NFEntry that should be modified
        :param NFEntry_2: NFEntry that should be modified
        :return: None
        """
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

    def accumulate(self, NFEntry_1, NFEntry_2) -> None:
        """
        This function accumulates parameters of the given NFEntry_2 to the NFEntry_1.

        :param NFEntry_1: NFEntry that should be accumulated
        :param NFEntry_2: NFEntry that should be accumulated
        :return: None
        """
        NFEntry_1.bidirectional_packets = float(NFEntry_1.bidirectional_packets) + float(NFEntry_2.bidirectional_packets)
        NFEntry_1.bidirectional_bytes = float(NFEntry_1.bidirectional_bytes) + float(NFEntry_2.bidirectional_bytes)
        NFEntry_1.bidirectional_duration_ms = float(NFEntry_1.bidirectional_duration_ms) + float(NFEntry_2.bidirectional_duration_ms)
        NFEntry_1.src2dst_packets = float(NFEntry_1.src2dst_packets) + float(NFEntry_2.src2dst_packets)
        NFEntry_1.src2dst_duration_ms = float(NFEntry_1.src2dst_duration_ms) + float(NFEntry_2.src2dst_duration_ms)
        NFEntry_1.dst2src_packets = float(NFEntry_1.dst2src_packets) + float(NFEntry_2.dst2src_packets)
        NFEntry_1.dst2src_duration_ms = float(NFEntry_1.dst2src_duration_ms) + float(NFEntry_2.dst2src_duration_ms)
        NFEntry_1.src2dst_bytes = float(NFEntry_1.src2dst_bytes) + float(NFEntry_2.src2dst_bytes)
        NFEntry_1.dst2src_bytes = float(NFEntry_1.dst2src_bytes) + float(NFEntry_2.dst2src_bytes)

    def append(self, NFEntry) -> None:
        """
        This function appends the given NFEntry to the buffer. Function checks the field that must be dropped
        in order to move element to buffer. After dropping the parameters the function checks if the element can be
        aggregated or not. If it can be aggregated then the function aggregates the element with the existing element
        in the buffer. If it cannot be aggregated then the function adds the element to the buffer.

        :param NFEntry: Element that should be added to the buffer
        :return:
        """
        if self.params is None:
            self.bufferedArray.append(NFEntry)
            return

        # Deleting param that is not needed in the buffer
        for element in self.params:
            delattr(NFEntry, element)

        # Checking if element can be aggregated or not
        # if not it will be added to the buffer
        if Buffer.containsEntry(self, NFEntry):
            NFEntry_1 = Buffer.containsEntry(self, NFEntry)
            self.takeMinimum(NFEntry_1=NFEntry_1, NFEntry_2=NFEntry)
            self.takeMaximum(NFEntry_1=NFEntry_1, NFEntry_2=NFEntry)
            self.accumulate(NFEntry_1=NFEntry_1, NFEntry_2=NFEntry)
            self.concatElements(NFEntry_1=NFEntry_1, NFEntry_2=NFEntry)
        else:
            self.bufferedArray.append(NFEntry)

            if self.advancedIPComparison == "True":
                if self.id not in [3, 4, 5]:
                    advanced_matching.add(root=self.root_src, word=advanced_matching.pre_process_ip_addr(NFEntry.src_ip))
                if self.id not in [4, 5]:
                    advanced_matching.add(root=self.root_dst,word=advanced_matching.pre_process_ip_addr(NFEntry.dst_ip))

    def delete(self, NFEntry) -> None:
        """
        This function deletes the given NFEntry from the buffer.

        :param NFEntry: NFEntry that should be deleted from the buffer
        :return: None
        """
        if self.advancedIPComparison == "True":
            if self.id not in [3, 4, 5]:
                advanced_matching.delete(root=self.root_src, word=advanced_matching.pre_process_ip_addr(NFEntry.src_ip))
            if self.id not in [4, 5]:
                advanced_matching.delete(root=self.root_dst, word=advanced_matching.pre_process_ip_addr(NFEntry.dst_ip))

        self.bufferedArray.remove(NFEntry)

    def getInformation(self) -> None:
        """
        Function to print the dropped values of the buffer.

        :return: None
        """
        outParams = ""
        for p in self.params:
            outParams += p + ","
        print(f'Buffer {self.id} following values dropped: {outParams}')

    def payload(self) -> int:
        """
        This function returns the payload size of the last element in the buffer. (bytes)

        :return: payload size of the last element in the buffer
        """
        return self.lastElement().bidirectional_bytes
        #return asizeof.asizeof(self.bufferedArray)

    def payloadInformation(self) -> None:
        """
        This function prints the payload size of the buffer.

        :return: None
        """
        print(f'Payload size in buffer {self.id} : {asizeof(self.bufferedArray)} bytes.')

    def getFlows(self) -> None:
        """
        This function prints the buffered array of the buffer.

        :return: None
        """
        print(f'Buffer {self.id}')
        for flow in self.bufferedArray:
            print(flow)

    def getFlowData(self) -> list:
        """
        This function returns the buffered array of the buffer.

        :return: buffered array of the buffer
        """
        return self.bufferedArray

    def moveable(self) -> bool:
        """
        This function checks if the buffer is moveable or not. If the buffer is moveable then it can be moved to
        another buffer.

        :return: True if the buffer is moveable, False otherwise
        """
        if len(self.bufferedArray) >= 2:
            return True
        return False
