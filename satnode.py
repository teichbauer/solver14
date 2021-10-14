# from typing_extensions import ParamSpecKwargs
from vklause import VKlause
from vk12mgr import VK12Manager
from tnode import TNode
from bitgrid import BitGrid
from center import Center
from node2 import Node2
from basics import ordered_dic_string


class SatNode:

    def __init__(self, parent, sh, vkm):
        choice = vkm.make_choice()  # avks be pooped out from vkm.vkdic
        self.parent = parent
        if parent:
            self.nov = parent.nov - 3
        else:
            self.nov = Center.maxnov
        self.sh = sh
        self.vkm = vkm
        Center.snodes[self.nov] = self
        self.next = None
        self.touched = choice['touched']
        self.next_sh = self.sh.reduce(choice["bits"])
        self.bgrid = BitGrid(choice)
        self.split_vkm()

    def split_vkm(self):
        """ 1. pop-out touched-vk3s forming sumvk2dic with them
            2. tdic: keyed by cvs of vks and values are lists of vks
               this results in self.vk2dics dict, keyed by the possible 
               grid-values(bgrid/chheads), vkdics restricting the value
               if vk2dics misses a chhead-value, that doesn't mean, this value
               if not allowed - quite the opposite: This means that there is no
               restriction(restrictive vk2) on this ch-head/value.
            3. make next-choice from vkm - if not empty, if it is empty,no .next
            """
        Center.satbits.update(self.bgrid.bitset)
        Center.bits = Center.bits - self.bgrid.bitset

        # sumvk2dic has all vk12s from touched.
        # each vk12 in here is referred by from vk12 in each self.vk12dics[v]
        self.sumvk12dic = {}
        # vk2dics: vkdics keyed by child-head-value
        self.vk12dics = {}
        for kn in self.touched:
            vk = self.vkm.pop_vk(kn)
            cvs, outdic = self.bgrid.cvs_and_outdic(vk)
            rvk = VKlause(vk.kname, outdic)
            for v in cvs:
                if v not in self.bgrid.covers:
                    vk12dic = self.vk12dics.setdefault(v, {})
                    vk12dic[kn] = rvk
                if kn not in self.sumvk12dic:
                    self.sumvk12dic[kn] = rvk

        if len(self.vkm.vkdic) > 0:
            # make next level (nov decrease 3) snode
            # self.vkm now has all vk3s
            self.next = SatNode(self,  # parent
                                self.next_sh.clone(),
                                self.vkm)
        else:
            self.back_path()
    # ---- def split_vkm(self) --------

    def back_path(self):
        pass

    def spawn(self):
        self.chdic = {}
        if not self.next:
            return self.solve()

        for gv in self.bgrid.chheads:
            vkd = self.vk2dics.get(gv, None)
            if vkd:
                if self.nov == 54 and gv == 1:
                    x = 1
                vkm = VK12Manager(vkd)
                n2 = Node2(vkm, self)
                n2.spawn()
            if vkd == None or not vkm.valid:
                continue

            if self.parent:
                dic = self.chdic.setdefault(gv, {})
                name0 = f"{self.nov}.{gv}"
                for pv, ptnode in self.parent.chdic.items():
                    if type(ptnode).__name__ == 'TNode':
                        if gv in ptnode.grps:
                            vkmx = vkm.clone()
                            if vkmx.add_vkdic(ptnode.grps[gv]):
                                tname = name0 + "-" + ptnode.name
                                dic[tname] = TNode(vkmx, self, tname)
                    elif type(ptnode).__name__ == 'dict':
                        for ky, tnd in ptnode.items():
                            if gv in tnd.grps:
                                tnd_vkm = VK12Manager(tnd.grps[gv])
                                m2 = Node2(tnd_vkm, self)
                                gvkms = m2.merge_node2(n2)
                                # else:
                                #     gvkms = n2.verify_merge(tnd_vkm)
                                if len(gvkms) == 0:
                                    continue
                                for index, vkm in gvkms.items():
                                    tname = name0 + f"-({ky})({index})"
                                    tnode = TNode(vkm, self, tname)
                                    dic[tname] = tnode
                x = 1
            else:
                self.chdic[gv] = TNode(vkm, self, f"{self.nov}.{gv}")

        Center.add_path_tnodes(self.chdic)
        if self.nov < 60:
            print(f"nov: {self.nov}")
            for chv, tnd in self.chdic.items():
                ln = len(tnd)
                print(f"{chv}: {ln}", end="   ")
            print()
        return self.next.spawn()

    def solve(self):
        for chv, tndic in self.parent.chdic.items():
            if len(tndic) == 0:
                continue
            for name, tn in tndic.items():
                tn.get_sats(self.bgrid)
        # Center.save_pathdic('path-fino1.json')
        return Center.sats
