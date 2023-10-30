from typing import Tuple


# TODO megvalositani valahogy hogy grafikusan megjelnjenek az egyes binaris fak
#   veszelyes tud lenni mert ha oriasi nagy akkor 2^32-en lesz
# https://towardsdatascience.com/implementing-a-trie-data-structure-in-python-in-less-than-100-lines-of-code-a877ea23c1a1
class Lulea_node():
    # Root letrehozasa az adott bufferhez
    def __init__(self, char:str):
        self.char = char
        self.children = []
        self.word_finished = False
        # hanyszor szerepel az adott szam
        self.counter = 1


def add(root, word:str):
    # egy ip cim hozzadasa az adott fahoz
    node = root
    for char in word:
        found_in_child = False
        for child in node.children:
            if child.char == char:
                child.counter+=1
                node = child
                found_in_child = True
                break
        if not found_in_child:
            new_node = Lulea_node(char=char)
            node.children.append(new_node)
            node = new_node
    node.word_finished = True


def delete(root, word:str):
    # Bool, int Tuple formatumban allnak elo az adatok
    # meg kell nezni megvan-e a prefix a faban, ha megvan akkor
    # vegig kell szaladni az egyes child nodeokon es -1 el kell csokkenteni
    # az adott node counterjet, abban az esetben ha ekkor a node counterje 0-ra
    # csokkenne akkor az adott nodeot torolni kell

    # megnezzuk benne van-e, ez vissza kell terjen True,1-el
    answ = find_prefix(root=root, prefix=word)

    # ha True ertekkel tert vissza akkor
    if answ[0] == True:
        node = root

        for char in word:
            found_in_child = False
            for child in node.children:
                # countereket csokkentjuk 1-el, ha 0-at elerik ki kell oket torolni
                if child.char == char:
                    child.counter -= 1
                    # ha 0 akkor mindegy mi van alatta mindent ki lehet dobni hiszen ez az egy rekord volt
                    if child.counter == 0:
                        node.children.remove(child)
                    # hanem akkor meg megyunk tovabb
                    node = child
                    found_in_child = True
                    break


def find_prefix(root, prefix:str) -> Tuple[bool, int]:
    node = root
    if not root.children:
        return False,0
    for char in prefix:
        char_not_found = True
        for child in node.children:
            if child.char == char:
                char_not_found = False
                node = child
                break
        if char_not_found:
            return False,0
    return True, node.counter


# ipv4-el mukodik csak
def pre_process_ip_addr(ip_addres):
    # "192.168.0.100" formatumban erkezik be stringkent
    # ezt szet kell szedni 4 darab 10es szamrendszerire
    # majd ezeket int-e castolni es atalkitani binarissa
    ip_addres_split = ip_addres.split('.')

    output = ""
    for octet in ip_addres_split:
        output += f'{int(octet):08b}'

    return output
