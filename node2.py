from vk12mgr import VK12Manager
from center import Center
from basics import get_bit


class Node2:
    def __init__(self, vkm, parent):
        self.parent = parent
        if type(vkm).__name__ == 'VK12Manager':
            self.vk1m, self.vkm = self.split_vkm(vkm.clone())
        elif type(vkm) == type({}):
            self.vk1m, self.vkm = self.split_vkm(VK12Manager(vkm))
        self.sat = {}
        if len(self.vk1m.vkdic) > 0:
            for vk1 in self.vk1m.vkdic.values():
                b, v = vk1.hbit_value()
                self.sat[b] = int(not v)
        self.chs = []  # [<0-th vkm>, <1-th vkm>]

    def add_sat(self, sat):
        self.sat.update(sat)
        return self

    def split_vkm(self, vk12m):
        vk1m = VK12Manager()
        while len(vk12m.kn1s) > 0:
            vk1 = vk12m.remove_vk1(vk12m.kn1s[0])
            if vk1:
                vk1m.add_vk1(vk1)
        return vk1m, vk12m  # vk12m is now vk2m

    def get_split_bit(self):
        max = 1
        maxbit = None
        bits = sorted(self.vkm.bdic.keys(), reverse=True)
        for b in bits:
            curr = len(self.vkm.bdic[b])
            if curr > max:
                max = curr
                maxbit = b
        return maxbit

    def spawn(self):
        mbit = self.get_split_bit()
        if not mbit:
            return None
        vkm0 = VK12Manager()  # subset of vks, for when mbit set to 0
        sat0 = {mbit: 0}
        vkm1 = VK12Manager()  # subset of vks, for when mbit set to 1
        sat1 = {mbit: 1}

        drp_kns = set(self.vkm.bdic.pop(mbit))
        kns = sorted(self.vkm.kn2s[:])  # all kns of vk2s in self.vkm
        for kn in drp_kns:
            kns.remove(kn)      # drop-out kn
            vk = self.vkm.vkdic.pop(kn)
            if vk.dic[mbit] == 0:
                vkm0.add_vk1(vk.drop_bit(mbit))
            else:
                vkm1.add_vk1(vk.drop_bit(mbit))
        for kn in kns:
            vk2 = self.vkm.vkdic.pop(kn)
            vkm0.add_vk2(vk2.clone())  # add_vk2 may modify vk2, clone, so
            vkm1.add_vk2(vk2)          # vkm1/add_vk2 won't have it wrong
        sd0 = set(self.vkm.bdic) - set(vkm0.bdic)
        for b in sd0:
            sat0[b] = 2
        sd1 = set(self.vkm.bdic) - set(vkm1.bdic)
        for b in sd1:
            sat1[b] = 2
        node0 = Node2(vkm0, self)
        node0.add_sat(sat0)
        node1 = Node2(vkm1, self)
        node1.add_sat(sat1)
        self.chs = [node0, node1]
        for n2 in self.chs:
            n2.spawn()

        return True
