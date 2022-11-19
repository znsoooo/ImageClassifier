"""Usage:
  1. Drag image folder(s) or file(s) into this window.
  2. Press direction key to show previous or next picture.
  3. Make classified folders in the directiory of this srcipt.
  4. Press `A-Z` or `0-9` to move picture into folder with same prefix letter.
  5. Click button with label to move picture into folder with same name.
  6. Press `Backspace/Esc/Delete` to undo last move.
  7. Pictures saved in the same directiory of this srcipt.
"""

import os
import wx
import xpinyin


__titie__ = 'Image Classifier'
__ver__   = 'v0.1.2'

exts = 'bmp;gif;ico;jpe;jpeg;jpg;png'


P = xpinyin.Pinyin()
exts = ['.' + ext for ext in exts.lower().split(';')]


def FindFolder(letter):
    if os.path.isdir(letter):
        return letter
    letter = letter.lower()
    names = [name for name in os.listdir() if os.path.isdir(name)]
    for name in names:
        if P.get_initial(name[0]).lower() == letter:
            return name
    os.makedirs(letter, exist_ok=True)
    return letter


def Walk(paths):
    paths = paths if isinstance(paths, list) else [paths]
    for path in paths:
        if os.path.isfile(path):
            if any(path.lower().endswith(ext) for ext in exts):
                yield path
        for root, folders, files in os.walk(path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in exts):
                    yield os.path.join(root, file)


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.OnDropFiles = lambda x, y, paths: parent.Add(paths)


class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.pics = []
        self.undo = []
        self.page = 0
        self.next = 0

        dt = MyFileDropTarget(self)
        self.SetDropTarget(dt)

        self.bmp = wx.StaticBitmap(self)
        self.txt = wx.StaticText(self)
        self.dock = wx.BoxSizer()

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.bmp, 1, wx.EXPAND)
        box.Add(self.txt, 1, wx.EXPAND | wx.ALL, 5)
        box.Add(self.dock, 0, wx.EXPAND)
        self.SetSizer(box)

        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_LEFT_DOWN,  lambda e: self.Flip(1))
        self.Bind(wx.EVT_RIGHT_DOWN, lambda e: self.Flip(-1))
        self.Bind(wx.EVT_MOUSEWHEEL, lambda e: self.Flip(1 if e.GetWheelRotation() < 0 else -1))

        self.Show()

        # for test
        # wx.CallAfter(self.Add, ['demo'])

    def Add(self, paths):
        for p in Walk(paths):
            if p not in self.pics:
                self.pics.append(p)
        self.Show()
        return True

    def Flip(self, n=None):
        n = n or self.next
        self.next = - (n < 0)
        self.page += n
        self.Show()

    def MoveTo(self, letter):
        if not self.pics:
            return
        src = self.pics.pop(self.page)
        dst = os.path.join(FindFolder(letter), os.path.basename(src))
        root, ext = os.path.splitext(dst)
        n = 1
        while os.path.exists(dst):
            n += 1
            dst = '%s-%d%s' % (root, n, ext)
        os.rename(src, dst)
        self.undo.append((src, dst))
        self.Flip()

    def Undo(self):
        if not self.undo:
            return
        src, dst = self.undo.pop()
        os.rename(dst, src)
        self.pics.insert(self.page, src)
        self.Show()

    def Show(self):
        for child in self.dock.GetChildren():
            child.GetWindow().Destroy()
        if self.pics:
            self.page = max(0, min(len(self.pics) - 1, self.page))
            path = self.pics[self.page]
            self.parent.SetTitle('(%d/%d) %s - %s %s' % (self.page + 1, len(self.pics), path, __titie__, __ver__))
            for name in os.listdir():
                if os.path.isdir(name):
                    btn = wx.Button(self, -1, name, size=(20, -1))
                    btn.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
                    btn.Bind(wx.EVT_BUTTON, self.OnButton)
                    self.dock.Add(btn, 1, wx.EXPAND)
            try:
                img = wx.Image(path)
                w, h = img.GetSize()
                w0, h0 = self.GetSize()
                rate = max(w / w0, h / h0)
                self.bmp.SetBitmap(wx.Bitmap(img.Rescale(int(w / rate), int(h / rate))))
                self.bmp.Show()
                self.txt.Hide()
            except wx.wxAssertionError as e:
                self.txt.SetLabel(str(e))
                self.txt.Show()
                self.bmp.Hide()
        else:
            self.parent.SetTitle(__titie__ + ' ' + __ver__)
            self.txt.SetLabel(__doc__)
            self.txt.Show()
            self.bmp.Hide()
        self.Layout()

    def OnButton(self, evt):
        btn = evt.GetEventObject()
        name = btn.GetLabel()
        self.MoveTo(name)

    def OnKeyUp(self, evt):
        id = evt.GetKeyCode()
        flip_map = {
            316: 1, 314: -1,
            317: 1, 315: -1,
            367: 10, 366: -10,
            312: 100, 313: -100,
        }
        if id in flip_map:
            self.Flip(flip_map[id])
        elif ord('A') <= id <= ord('Z') or ord('0') <= id <= ord('9'):
            self.MoveTo(chr(id))
        elif 323 < id < 334: # num pad
            self.MoveTo(chr(id - 276))
        elif id in (8, 27, 127): # Backspace/Esc/Delete
            self.Undo()


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, size=(1200, 800))
        self.panel = MyPanel(self)
        self.Center()
        self.Show()


if __name__ == '__main__':
    app = wx.App()
    frm = MyFrame()
    app.MainLoop()
