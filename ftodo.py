#!/usr/bin/env python3

from datetime import datetime, timedelta
import shelve, math
import os, sys
import re

itemdb="/Users/ak/Dropbox/etodo/todoitems"
# itemdb="todoitems.db"
itemdb = "todoitems"

"""
status codes: 1 - normal; 2 - done
"""

class Item:
    def __init__(self, n):
        self.name=n
        self.created = datetime.now()
        self.fade = self.created+timedelta(hours=24)
        self.expire = self.created+timedelta(hours=72)
        self.status=1

    def __repr__(self):
        expires_in = self.expire - datetime.now()

        # show time when less than 12 hours left
        if self.status == 1 and 0 < expires_in.total_seconds() < 12*3600:
            return self.with_time()
        return self.name

    def with_time(self):
        def y(a): return str(int(math.floor(a)))
        x = self.expire-datetime.now()
        m = x.total_seconds()/60
        h,m = m//60,m%60
        return self.name +' '+y(h)+':'+y(m)#+' exp: '+str(self.expire)


class Items:
    def __init__(self):
        s = shelve.open(itemdb)
        items = s.get('items') or []
        self.folders = s.get('folders')
        if not self.folders:
            self.folders = dict(main=items)
        if 'a' in self.folders and not 'main' in self.folders:
            self.folders['main'] = self.folders["a"]
        self.current_folder = s.get('current_folder') or 'main'
        if self.current_folder=='a':
            self.current_folder = 'main'
        self.items = self.folders[self.current_folder]

    def add_folder(self, name):
        if name not in self.folders:
            self.folders[name] = []
            self.set_current_folder(name)
        else:
            print('"%s" folder already exists' % name)

    def delete_folder(self, name):
        if self.current_folder == name:
            print("Error: cannot remove active (current) folder.")
        elif name not in self.folders:
            print("Error: no such folder!")
        else:
            del self.folders[name]

    def set_current_folder(self, name):
        flds = [f for f in self.folders.keys() if f.lower().startswith(name.lower())]
        if len(flds)>1:
            print("More than one match: %s"%', '.join(flds))
        elif not flds:
            print("Folder not found; available folders: %s" % ', '.join(self.folders.keys()))
        else:
            name = flds[0]
            self.folders[self.current_folder] = self.items
            self.items = self.folders[name]
            self.current_folder = name

    def save(self):
        s = shelve.open(itemdb)
        # print("self.items", self.items)
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
        return [i for i in self.items if i.fade < datetime.now() < i.expire and i.status==1]

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
                        if len(self.items_)<11:
                            print("{0}) {1}".format(n,i))
                        else:
                            print("{0:>2}) {1}".format(n,i))
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
        i = i.strip()
        cmds = dict(a='add', R='delete', d='done', f='fade', e='expire', b='bump', E='expired', h='help', D='list_done', r='rename', o='folder',
                    # double letter commands
                    EE='empty_expired', AF='add_folder', lf='list_folders', RF='delete_folder',
                    )

        # these commands should skip listing current items because user needs to see their output
        # (i.e. not to have it scrolled up and hidden)
        skip_listing = "h D EE AF lf RF".split()

        single_match = re.match('^(\D)$', i)
        # n+ number index arguments
        num_arg_match = re.match('^(\D+) ?([\d ]+)$', i)
        # with optional string arg
        arg_match = re.match('^([\w]+) ?(.+)?$', i)
        arg = None
        if single_match:
            cmd = single_match.groups()[0]

        if single_match and cmd in cmds:
            pass
        elif num_arg_match:
            cmd, arg = num_arg_match.groups()
            arg = [int(x) for x in arg.strip().split()]
        elif arg_match:
            g = list(arg_match.groups())
            cmd = g.pop(0)
            if g:
                arg = g.pop()
        cmd = cmd.strip()
        # print("cmd", cmd)
        # print("arg", arg)

        self.skip_listing = True    # listing is skipped on any error and most commands except those in `skip_listing`
        if cmd in cmds:
            try:
                getattr(self, cmds[cmd])(arg)
                if cmd not in skip_listing:
                    self.skip_listing = False
            except Exception as e:
                print("ERROR: %s"%e)
        else:
            print("ERROR: Command not found: %s"%cmd)

    def help(self, arg):
        print("""
          a)dd
          R)remove
          d)one
          f)ade
          f o)lder
          e)xpire
          b)ump
          E)xpired list
          EE) empty expired
          AF) add folder
          RF) remove folder
          lf) list folders
          D)one list
          r)ename
          h)elp""")

    def list_folders(self, arg):
        print()
        print(' '.join(items.folders.keys()))
        print('\n'*3)

    def list_done(self, arg):
        it = items.done()
        for n,i in enumerate(it):
            print(i)

    def add(self, name):
        items.add(Item(name.strip()))
        print('\n'*3)

    def delete(self, indexes):
        for i in reversed(sorted(indexes)):
            i = int(i)-1
            it = list(filter(None, self.items_))
            x= it[i]
            # print('removing ',x)
            items.items.remove(x)
            # print("items.items", items.items)

    def done(self, indexes):
        for i in indexes:
            i = int(i)-1
            i = list(filter(None, self.items_))[i]
            i.status=2

    def rename(self, indexes):
        for i in indexes:
            i = int(i)-1
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

    def delete_folder(self, name):
        i = input("WARNING! Are you sure you wish to remove folder '%s' [Y/N]? " % name)
        if i=='Y':
            items.delete_folder(name)
            print("Removed folder '%s'" % name)

    def folder(self, name):
        items.set_current_folder(name)

    def fade(self, indexes):
        for i in indexes:
            i = int(i)-1
            i = list(filter(None, self.items_))[i]
            i.fade = datetime.now()
            i.expire = datetime.now()+timedelta(hours=24)

    def expire(self, indexes):
        for i in indexes:
            i = int(i)-1
            i = list(filter(None, self.items_))[i]
            i.fade = datetime.now()-timedelta(hours=24)
            i.expire = datetime.now()

    def bump(self, indexes, items_=None):
        for i in indexes:
            i = int(i)-1
            items_ = items_ or self.items_
            i = list(filter(None, items_))[i]

            i.fade = datetime.now()+timedelta(hours=24)
            i.expire = datetime.now()+timedelta(hours=72)

    def empty_expired(self, arg):
        for item in items.expired():
            items.remove(item)
        print("emptied expired items")

    def expired(self, arg):
        it = items.expired()
        self.skip_listing = 1
        if not it:
            print("No expired items")
            return
        for n,i in enumerate(it):
            print("{0}) {1}".format(n+1,i))

        idx = input('bump> ').strip().split()
        if not idx:
            return
        if idx[0]=='q':
            self.quit()
        try:
            self.bump(idx, items_=it)
        except Exception as e:
            print("Error: %s"%e)


if __name__=='__main__':
    # print("itemdb", itemdb)
    items = Items()
    etodo = ETodo()
    etodo.main()
