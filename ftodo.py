#!/usr/bin/env python3

from datetime import datetime, timedelta
import shelve, math
import os, sys

itemdb="/Users/ak/Dropbox/etodo/todoitems"
# itemdb="todoitems.db"
itemdb="todoitems"

class Item:
    def __init__(self, n):
        self.name=n
        self.created = datetime.now()
        self.fade = self.created+timedelta(hours=24)
        self.expire = self.created+timedelta(hours=72)
        self.status=1

    def __repr__(self):
        expires_in = self.expire - datetime.now()
        if self.status == 1 and 0 < expires_in.total_seconds() < 12*3600:
            return self.with_time()
        return self.name

    def with_time(self):
        def y(a): return str(int(math.floor(a)))
        x = self.expire-datetime.now()
        m = x.total_seconds()/60
        h,m=m//60,m%60
        return self.name +' '+y(h)+':'+y(m)#+' exp: '+str(self.expire)


class Items:
    def __init__(self):
        s = shelve.open(itemdb)
        self.items = s.get('items') or []
        self.folders = s.get('folders') or dict(a=self.items)
        self.current_folder = s.get('current_folder') or 'a'
        self.items = self.folders[self.current_folder]

        # print("self.items", self.items)

    def add_folder(self, name):
        if name not in self.folders:
            self.folders[name] = []
            self.set_current_folder(name)
        else:
            print('"%s" folder already exists' % name)

    def set_current_folder(self, name):
        if name in self.folders:
            self.folders[self.current_folder] = self.items
            self.items = self.folders[name]
            self.current_folder = name
        else:
            print('Folder not found; available folders: %s' % ' '.join(self.folders.keys()))

    def save(self):
        s = shelve.open(itemdb)
        # print("self.items", self.items)
        s['items'] = self.items
        s['folders'] = self.folders
        s['current_folder'] = self.current_folder
        s.close()

    def add(self, i):
        self.items.append(i)

    def delete(self, i):
        del items[i]

    def __iter__(self):
        return iter(self.items[1:])

    def normal(self):
        return [i for i in self.items if i.fade >= datetime.now() and i.status==1]

    def done(self):
        return [i for i in self.items if i.status==2]

    def faded(self):
        """These will disappear within 24hr."""
        return [i for i in self.items if i.fade < datetime.now() < i.expire and i.status ==1]

    def expired(self):
        return [i for i in self.items if datetime.now() >= i.expire and i.status==1]

    def remove(self, i):
        self.items.remove(i)


class ETodo:
    skip_listing=0
    def main(self):
        while True:
            # print(items.items)
            self.items_ = items.normal() + [None] + items.faded()
            n=1
            if not self.skip_listing:
                for i in self.items_:
                    if i is None:
                        print()
                    else:
                        print("{0}) {1}".format(n,i))
                        n+=1
            self.skip_listing=0

            i = input('[%s] > ' % items.current_folder).strip()
            if not i:
                print('\n'*3)
                continue
            if i=='q':
                self.quit()
            self.cmd(i)

    def quit(self):
        items.save()
        print("Items saved!")
        sys.exit()

    def cmd(self, i):
        cmds = dict(a='add',R='delete',d='done',f='fade',e='expire',b='bump',E='expired',h='help',D='list_done', EE='empty_expired', r='rename',
                    AF='add_folder', o='folder', lf='list_folders')
        num=None
        if len(i)>1:
            try:
                num = int(i[1:].strip())-1
            except:
                pass
        try:
            if i=='EE':
                self.empty_expired()
            elif i=='lf':
                self.list_folders()
            elif i.startswith('AF'):
                self.add_folder(i[2:].strip()[0])
            elif num is not None:
                getattr(self, cmds[i[0]])(num)
            else:
                getattr(self, cmds[i[0]])(i[1:])
        except Exception as e:
            print("error:",e)
            raise e
            pass

    def help(self,i):
        print("""
          a)dd
          R)remove
          d)one
          f)ade
          fo)lder
          e)xpire
          b)ump
          E)xpired list
          EE) empty expired
          AF) add folder
          lf) list folders
          D)one list
          r)ename
          h)elp""")
        self.skip_listing=1

    def list_folders(self):
        print()
        print(' '.join(items.folders.keys()))
        print('\n'*3)

    def list_done(self, i):
        it = items.done()
        for n,i in enumerate(it):
            print("{0}) {1}".format(n+1,i))

    def add(self, name):
        items.add(Item(name.strip()))
        print('\n'*3)

    def delete(self, i):
        it = list(filter(None, self.items_))
        x= it[i]
        # print('removing ',x)
        items.items.remove(x)
        # print("items.items", items.items)

    def done(self, i):
        self.items_[i].status=2

    def rename(self, i):
        print('Rename')
        it = list(filter(None, self.items_))
        x = it[i]
        print(x.name)
        new = input('New > ')
        if new.strip():
            x.name = new.strip()
        print('\n'*3)


    def add_folder(self, name):
        items.add_folder(name)

    def folder(self, name):
        items.set_current_folder(name)

    def fade(self, i):
        self.items_[i].fade = datetime.now()
        self.items_[i].expire = datetime.now()+timedelta(hours=24)

    def expire(self, i):
        self.items_[i].fade = datetime.now()-timedelta(hours=24)
        self.items_[i].expire = datetime.now()

    def bump(self, i, items = None):
        items = items or self.items_
        i = list(filter(None,items))[i]

        i.fade = datetime.now()+timedelta(hours=24)
        i.expire = datetime.now()+timedelta(hours=72)

    def empty_expired(self):
        for item in items.expired():
            items.remove(item)
        print("emptied expired items")

    def expired(self,i):
        it = items.expired()
        if not it:
            print("No expired items")
            return
        for n,i in enumerate(it):
            print("{0}) {1}".format(n+1,i))

        idx = input('bump> ').strip().split()
        for i in idx:
            self.bump(int(i)-1, items = it)


if __name__=='__main__':
    print("itemdb", itemdb)
    items = Items()
    etodo = ETodo()
    etodo.main()
