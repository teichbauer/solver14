from vk12mgr import VK12Manager
from center import Center
from basics import get_bit


class Node2:
    def __init__(self, vkm, parent, name, sat={}):
        self.parent = parent
        if type(parent).__name__ == 'Node2':
            self.root = parent.root
            self.sats = parent.sats[:]
        else:
            self.root = self
            self.sats = []
        if type(vkm).__name__ == 'VK12Manager':
            self.vk1m, self.vkm = self.split_vkm(vkm.clone())
        elif type(vkm) == type({}):
            self.vk1m, self.vkm = self.split_vkm(VK12Manager(vkm))

        if type(name) == type(0):
            self.splitbit = name
            self.name = 'root'
        else:
            self.name = name
            self.splitbit = self.vkm.pick_sbit()

        if len(self.vk1m.vkdic) > 0:
            for vk1 in self.vk1m.vkdic.values():
                b, v = vk1.hbit_value()
                sat[b] = int(not v)
        if len(sat) > 0:
            self.sats.append(sat)
        self.chs = []  # [<0-th vkm>, <1-th vkm>]

    def split_vkm(self, vk12m):
        vk1m = VK12Manager()
        while len(vk12m.kn1s) > 0:
            vk1 = vk12m.remove_vk1(vk12m.kn1s[0])
            if vk1:
                vk1m.add_vk1(vk1)
        return vk1m, vk12m  # vk12m is now vk2m

    def spawn(self):
        if not self.splitbit:
            self.root.sats.append(self.sats)
            return None
        vkm0 = VK12Manager()  # subset of vks, for when mbit set to 0
        sat0 = {self.splitbit: 0}
        vkm1 = VK12Manager()  # subset of vks, for when mbit set to 1
        sat1 = {self.splitbit: 1}

        drp_kns = set(self.vkm.bdic[self.splitbit])
        kns = sorted(self.vkm.kn2s[:])  # all kns of vk2s in self.vkm
        for kn in drp_kns:
            kns.remove(kn)      # drop-out kn
            vk = self.vkm.vkdic.pop(kn)
            if vk.dic[self.splitbit] == 0:
                vkm0.add_vk1(vk.drop_bit(self.splitbit))
            else:
                vkm1.add_vk1(vk.drop_bit(self.splitbit))
        for kn in kns:
            vk2 = self.vkm.vkdic.pop(kn)
            vkm0.add_vk2(vk2.clone())  # add_vk2 may modify vk2, clone, so
            vkm1.add_vk2(vk2)          # vkm1/add_vk2 won't have it wrong
        sd0 = set(self.vkm.bdic) - set(vkm0.bdic)
        for b in sd0:
            if b != self.splitbit:
                sat0[b] = 2
        sd1 = set(self.vkm.bdic) - set(vkm1.bdic)
        for b in sd1:
            if b != self.splitbit:
                sat1[b] = 2
        name0 = f"{self.name}-{self.splitbit}.0"
        node0 = Node2(vkm0, self, name0, sat0)
        # node0.sat.update(sat0)
        name1 = f"{self.name}-{self.splitbit}.1"
        node1 = Node2(vkm1, self, name1, sat1)
        # node1.sat.update(sat1)
        node0.spawn()
        node1.spawn()
        self.chs = node0, node1  # tuple of 2 children

        return True

    def display(self):
        m = f"{self.sats}->{self.splitbit} : "
        m += f"{len(self.vkm.bdic)}/{len(self.vkm.vkdic)}"
        return m

    def collect_sats(self, sats=[]):
        for sat in sats:
            sat.update(self.sat)
        for ch in self.chs:
            ch.collect_sats(sats)
        return sats
