#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import re
import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import shortcut, showInfo, showText, tooltip
# import trackback
from mdict.mdict_query import IndexBuilder
from collections import defaultdict
import wquery.context as c

index_builders = defaultdict(int)


class MdxIndexer(QThread):

    def __init__(self, ix):
        QThread.__init__(self)
        self.ix = ix

    def run(self):
        if self.ix == -1:
            # index all dicts
            for i, each in enumerate(c.maps):
                if each['checked'] and each["dict_path"]:
                    index_builders[i] = self.work(each["dict_path"])
        else:
            # only index given dict, specified by ix
            index_builders[self.ix] = self.work(c.maps[self.ix]["dict_path"])

    def work(self, dict_path):
        # showInfo("%d, %s" % (self.ix, dict_path))
        if not dict_path.startswith("http://"):
            index_builder = IndexBuilder(dict_path)
            errors, styles = save_media_files(index_builder, '*.css', '*.js')
            # if '*.css' in errors:
            # info = ' '.join([each[2:] for each in ['*.css', '*.js'] if
            # each in errors ])
            # tooltip(u"%s字典中缺失css文件，格式显示可能不正确，请自行查找文件并放入媒体文件夹中" %
            #         (dict_path), period=3000)
            return index_builder


def index_mdx(ix=-1):
    mw.progress.start(immediate=True, label="Index building...")
    index_thread = MdxIndexer(ix)
    index_thread.start()
    while not index_thread.isFinished():
        mw.app.processEvents()
        index_thread.wait(100)
    mw.progress.finish()


def query():
    if c.context['type'] == 'editor':
        editor = c.context['obj']
        c.model_id = editor.note.model()['id']
        word = editor.note.fields[0]
        c.maps = c.mappings[c.model_id]
        # showText(str(c.mappings))
        # showInfo('%s, %s, %s, %s' %
        #          (word, editor.note.model()['name'], str(c.model_id), str(c.maps)))
        for i, res in query_all_flds(word):
            if res == "":
                if c.update_all:
                    editor.note.fields[i] = res
            else:
                editor.note.fields[i] = res
        editor.note.flush()
        editor.setNote(editor.note, focus=True)
        mw.requireReset()
        # browser = c.context.get('action', '')
        # if browser:

    if c.context['type'] == 'browser':
        browser = c.context['obj']
        notes = [browser.mw.col.getNote(note_id)
                 for note_id in browser.selectedNotes()]
        mw.progress.start(immediate=True, label="Querying...")
        for i, note in enumerate(notes):
            word = note.fields[0]
            c.model_id = note.model()['id']
            c.maps = c.mappings[c.model_id]
            for j, res in query_all_flds(word):
                if res == "":
                    if c.update_all:
                        note.fields[j] = res
                else:
                    note.fields[j] = res
                note.flush()
            mw.progress.update(label="Queried %d words..." % (i + 1))

        mw.progress.finish()
        if len(notes) > 1:
            tooltip(u'共更新 %d 张卡片' % len(notes))


def query_all_flds(word):
    for i, each in enumerate(c.maps):
        res = ""
        if i == 0:
            res = word
        else:
            if each['checked'] and each['dict_path'].strip():
                res = query_mdict(word, i, **each)
        yield i, res


def query_mdict(word, ix, **kwargs):
    dict_path, fld_name = kwargs.get(
        'dict_path', '').strip(), kwargs.get('fld_name', '').strip()
    use_server = dict_path.startswith("http://")
    use_local = not use_server
    if use_local:
        if not index_builders[ix]:
            index_mdx(ix)
        result = index_builders[ix].mdx_lookup(word)
        if result:
            return update_dict_field(ix, result[0], index_builders[ix])
    else:
        req = urllib2.urlopen(serveraddr + r'/' + word)
        return update_dict_field(ix, req.read())
    return ""


def update_dict_field(idx, text, ib=0):
    return convert_media_path(ib, text) if ib else text


def save_media_files(ib, *args, **kwargs):
    """
    only get the necessary static files
    ** kwargs: data = list
    """
    lst = []
    errors = []
    styles = []
    wild = list(args) + ['*' + os.path.basename(each)
                         for each in kwargs.get('data', [])]
    try:
        for each in wild:
            keys = ib.get_mdd_keys(each)
            if not keys:
                errors.append(each)
            lst.extend(keys)
        # showInfo(str(errors))
        media_dir = mw.col.media.dir()
        for each in lst:
            try:
                bytes_list = ib.mdd_lookup(each)
                if bytes_list:
                    savepath = os.path.join(
                        media_dir, '_' + os.path.basename(each))
                    if os.path.basename(each).endswith('.css') or os.path.basename(each).endswith('.js'):
                        styles.append(os.path.basename(each))
                    if not os.path.exists(savepath):
                        with open(savepath, 'wb') as f:
                            f.write(bytes_list[0])
            except sqlite3.OperationalError as e:
                showInfo(str(e))
        # showInfo(str(styles))
    except AttributeError:
        '''
        有些字典会出这样的错误u AttributeError: 'IndexBuilder' object has no attribute '_mdd_db'
        '''
        pass
    return errors, styles


def convert_media_path(ib, html):
    """
    convert the media path to actual path in anki's collection media folder.'
    """
    # showInfo('%s %s' % (type(html), str(html)))
    lst = list()
    mcss = re.findall('href="(\S+?\.css)"', html)
    lst.extend(list(set(mcss)))
    mjs = re.findall('src="([\w\./]\S+?\.js)"', html)
    lst.extend(list(set(mjs)))
    msrc = re.findall('<img.*?src="([\w\./]\S+?)".*?>', html)
    lst.extend(list(set(msrc)))
    errors, styles = save_media_files(ib, data=list(set(lst)))
    # showInfo(str(styles))
    # showInfo(str(list(set(msrc))))
    # print lst
    newlist = ['_' + each.split('/')[-1] for each in lst]
    # print newlist
    for each in zip(lst, newlist):
        html = html.replace(each[0], each[1])
    html = '<br>'.join(["<style>@import url('_%s');</style>" %
                        style for style in styles if style.endswith('.css')]) + html
    html += '<br>'.join(['<script type="text/javascript" src="_%s"></script>' %
                         style for style in styles if style.endswith('.js')])
    # showInfo(str(html))
    # showInfo(html)
    return unicode(html)