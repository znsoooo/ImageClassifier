import os
import wx
import xpinyin


__titie__ = 'Image Classifier'
__ver__   = 'v0.1.0'

exts = 'bmp;gif;ico;jpe;jpeg;jpg;png'


P = xpinyin.Pinyin()
exts = ['.' + ext for ext in exts.lower().split(';')]


def FindFolder(letter):
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
        self.page = 0
        self.next = 0

        dt = MyFileDropTarget(self)
        self.SetDropTarget(dt)

        self.bmp = wx.StaticBitmap(self)
        box = wx.BoxSizer()
        box.Add(self.bmp, 1, wx.EXPAND | wx.ALL)
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
        self.page = max(0, min(len(self.pics) - 1, self.page + n))
        self.Show()

    def Move(self, id, letter):
        src = self.pics.pop(id)
        dst = os.path.join(FindFolder(letter), os.path.basename(src))
        root, ext = os.path.splitext(dst)
        n = 1
        while os.path.exists(dst):
            n += 1
            dst = '%s-%d%s' % (root, n, ext)
        os.rename(src, dst)
        self.Flip()

    def Show(self):
        if self.pics:
            path = self.pics[self.page]
            self.parent.SetTitle('(%d/%d) %s - %s %s' % (self.page + 1, len(self.pics), path, __titie__, __ver__))
            try:
                img = wx.Image(path)
                w, h = img.GetSize()
                w0, h0 = self.GetSize()
                rate = max(w / w0, h / h0)
                self.bmp.SetBitmap(wx.Bitmap(img.Rescale(int(w / rate), int(h / rate))))
                self.bmp.Show()
            except wx.wxAssertionError:
                self.bmp.Hide()
        else:
            self.parent.SetTitle(__titie__ + ' ' + __ver__)
            self.bmp.Hide()
        self.Layout()

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
            self.Move(self.page, chr(id))
        elif 323 < id < 334: # num pad
            self.Move(self.page, chr(id - 276))


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
