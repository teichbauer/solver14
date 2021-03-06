from vklause import VKlause
from vk12mgr import VK12Manager
from center import Center
from basics import get_bit


class Node2:
    def __init__(self, vkm, parent, name='root'):
        if type(vkm).__name__ == 'VK12Manager':
            self.vk1m, self.vkm = self.split_vkm(vkm.clone())
        elif type(vkm) == type({}):
            self.vk1m, self.vkm = self.split_vkm(VK12Manager(vkm))
        self.parent = parent
        if type(parent).__name__ == 'Node2':
            self.root = parent.root
            # self.sats = parent.sats[:]
            for kn in parent.vk1m.kn1s:
                self.vk1m.add_vk1(parent.vk1m.vkdic[kn])
        else:
            self.root = self
            self.end_node2s = []

        self.splitbit = self.pick_sbit()
        self.name = name
        self.chs = []  # [<0-th vkm>, <1-th vkm>]
        self.grps = {}

    def pick_sbit(self):
        # find bit with most overlapping vk2s
        max = 1
        maxbit = None
        bits = sorted(self.vkm.bdic.keys(), reverse=True)
        for b in bits:
            ln = len(self.vkm.bdic[b])
            if ln > max:
                max = ln
                maxbit = b
        return maxbit

    def sat_hit_test(self, sat):
        sbits = set(sat)
        s1 = sbits.intersection(self.vk1m.bdic)
        for b in s1:
            for kn, vk1 in self.vk1m.vkdic.items():
                if vk1.hit(sat):
                    return True
        s2 = sbits.intersection(self.vkm.bdic)
        if len(s2) > 2:
            for kn, vk2 in self.vkm.vkdic.items():
                if s2.issuperset(vk2.bits):
                    if vk2.hit(sat):
                        return True
        return False

    def split_vkm(self, vk12m):
        vk1m = VK12Manager()
        while len(vk12m.kn1s) > 0:
            vk1 = vk12m.remove_vk1(vk12m.kn1s[0])
            if vk1:
                vk1m.add_vk1(vk1)
        return vk1m, vk12m  # vk12m is now vk2m

    def verify_vk1s(self, node):
        shared_bits = set(self.vk1m.bdic).intersection(node.vk1m.bdic)
        for bit in shared_bits:
            names = self.vk1m.bdic[bit]
            xnames = node.vk1m.bdic[bit]
            for n in names:
                for xn in xnames:
                    v = self.vk1m.vkdic[n].hbit_value()[1]
                    xv = node.vk1m.vkdic[xn].hbit_value()[1]
                    if v != v:
                        return False
        return True

    def spawn(self):
        if not self.splitbit:
            self.root.end_node2s.append(self)
            return None
        vkm0 = VK12Manager()  # subset of vks, for when mbit set to 0
        vkm0.add_vk1(VKlause(f"{self.splitbit}.0", {self.splitbit: 1}))
        vkm1 = VK12Manager()  # subset of vks, for when mbit set to 1
        vkm1.add_vk1(VKlause(f"{self.splitbit}.1", {self.splitbit: 0}))

        drp_kns = set(self.vkm.bdic[self.splitbit])
        kns = sorted(self.vkm.kn2s[:])  # all kns of vk2s in self.vkm

        # process vks sitting on splitbit
        for kn in drp_kns:
            kns.remove(kn)      # drop-out kn
            vk = self.vkm.vkdic[kn].clone()
            if vk.dic[self.splitbit] == 0:
                vkm0.add_vk1(vk.drop_bit(self.splitbit))
            else:
                vkm1.add_vk1(vk.drop_bit(self.splitbit))

        # add vks not touched by splitbit
        for kn in kns:
            vk2 = self.vkm.vkdic[kn]
            vkm0.add_vk2(vk2.clone())  # add_vk2 may modify vk2, clone, so
            vkm1.add_vk2(vk2.clone())  # vkm1/add_vk2 won't have it wrong
        node0 = Node2(vkm0, self, f"{self.name}-{self.splitbit}.0")
        node1 = Node2(vkm1, self, f"{self.name}-{self.splitbit}.1")

        node0.spawn()
        node1.spawn()
        self.chs = node0, node1  # tuple of 2 children
        return True

    def verify_merge(self, tnd_vkm):
        goods = {}
        for ind, n2 in enumerate(self.end_node2s):
            vkm = tnd_vkm.clone()
            # thru = True
            kn1s = n2.vk1m.kn1s[:]
            while len(kn1s) > 0:
                kn = kn1s.pop(0)
                if kn in vkm.vkdic:
                    vkm.remove_vk(kn)
                vk1 = n2.vk1m.vkdic[kn].clone()
                added = vkm.add_vk1(vk1)
                if not vkm.valid:
                    break
            if not vkm.valid:
                continue
            kn2s = n2.vkm.kn2s[:]
            while len(kn2s) > 0:
                vk = n2.vkm.vkdic[kn2s.pop(0)].clone()
                added = vkm.add_vk2(vk)
                if not vkm.valid:
                    break
            if not vkm.valid:
                continue
            goods[ind] = vkm
        return goods

    def merge_node2(self, n2):
        goods = {}
        for ind, node in enumerate(n2.end_node2s):
            if self.verify_vk1s(node):
                goods[ind] = node.vkm
        return goods

    def get_sat(self, index=None):
        if index == None:
            lst = []
            ln = len(self.root.sats)
            for i in range(ln):
                sat = self.get_sat(i)
                lst.append(sat)
            return lst
        else:
            lst = self.root.sats[index]
            dic = {}
            for st in lst:
                dic.update(st)
            return dic

    def display(self):
        m = f"{self.sats}->{self.splitbit} : "
        m += f"{len(self.vkm.bdic)}/{len(self.vkm.vkdic)}"
        return m
