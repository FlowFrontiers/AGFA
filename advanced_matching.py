from typing import Tuple


class Lulea_node:
    """
    Lulea node for the trie.
    This implementation is based on the following article:
    https://towardsdatascience.com/implementing-a-trie-data-structure-in-python-in-less-than-100-lines-of-code-a877ea23c1a1
    """

    def __init__(self, char: str) -> None:
        self.char = char
        self.children = []
        self.word_finished = False
        # hanyszor szerepel az adott szam
        self.counter = 1


def add(root, word: str) -> None:
    """
    Adding an IP address to the tree.

    :param root: the root of the trie
    :param word: given IP address
    :return: None
    """
    node = root
    for char in word:
        found_in_child = False
        for child in node.children:
            if child.char == char:
                child.counter += 1
                node = child
                found_in_child = True
                break
        if not found_in_child:
            new_node = Lulea_node(char=char)
            node.children.append(new_node)
            node = new_node
    node.word_finished = True


def delete(root, word: str) -> None:
    """
    Deleting an IP address from the tree.

    :param root: root of the trie
    :param word: given IP address that should be deleted
    :return: None
    """
    answ = find_prefix(root=root, prefix=word)
    if answ[0]:
        node = root
        for char in word:
            found_in_child = False
            for child in node.children:
                if child.char == char:
                    child.counter -= 1
                    if child.counter == 0:
                        node.children.remove(child)
                    node = child
                    found_in_child = True
                    break


def find_prefix(root, prefix: str) -> Tuple[bool, int]:
    """
    Finding the given prefix in the tree.

    :param root: root of the trie
    :param prefix: prefix that should be found in the tree
    :return: state of the found, number of the occurrences
    """
    node = root
    if not root.children:
        return False, 0
    for char in prefix:
        char_not_found = True
        for child in node.children:
            if child.char == char:
                char_not_found = False
                node = child
                break
        if char_not_found:
            return False, 0
    return True, node.counter


def pre_process_ip_addr(ip_address: str) -> str:
    """
    Preprocessing the IP address to binary format. The IP address is split by dots and each octet is converted to
    binary format. It can be used only with IPv4 protocol.
    :param ip_address:
    :return:
    """
    ip_address_split = ip_address.split('.')

    output = ""
    for octet in ip_address_split:
        output += f'{int(octet):08b}'

    return output
