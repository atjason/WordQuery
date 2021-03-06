#-*- coding:utf-8 -*-
import re
import urllib2

from aqt.utils import showInfo, showText
from BeautifulSoup import BeautifulSoup
from cookielib import CookieJar

from .base import WebService, export, with_styles, register


@register(u'Bing')
class Bing(WebService):

    def __init__(self):
        super(Bing, self).__init__()
        self.cj = CookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cj))

    def _get_content(self):
        headers = {
            'Accept-Language': 'en-US,zh-CN;q=0.8,zh;q=0.6,en;q=0.4',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        result = {}
        # try:
        # if not self.cj:
        request = urllib2.Request(
            'http://cn.bing.com/dict/', headers=headers)
        self.opener.open(request).read()
        request = urllib2.Request(
            "http://cn.bing.com/dict/search?q=%s" % self.word, headers=headers)
        html = self.opener.open(request).read()
        soup = BeautifulSoup(html)

        def _get_element(soup, tag, id=None, class_=None, subtag=None):
            # element = soup.find(tag, id=id, class_=class_)  # bs4
            element = None
            if id:
                element = soup.find(tag, {"id": id})
            if class_:
                element = soup.find(tag, {"class": class_})
            if subtag and element:
                element = getattr(element, subtag, '')
            return element

        element = _get_element(soup, 'div', class_='hd_prUS')
        if element:
            result['phonitic_us'] = str(element).decode('utf-8')
        element = _get_element(soup, 'div', class_='hd_pr')
        if element:
            result['phonitic_uk'] = str(element).decode('utf-8')
        element = _get_element(soup, 'div', class_='hd_if')
        if element:
            result['participle'] = str(element).decode('utf-8')
        element = _get_element(soup, 'div', class_='qdef', subtag='ul')
        if element:
            result['def'] = u''.join([str(content).decode('utf-8')
                                      for content in element.contents])
        #    for pair in pairs])
        # result = _get_from_element(
        #     result, 'advanced_ec', soup, 'div', id='authid')
        # result = _get_from_element(
        #     result, 'ec', soup, 'div', id='crossid')
        # result = _get_from_element(
        #     result, 'ee', soup, 'div', id='homoid')
        # result = _get_from_element(
        #     result, 'web_definition', soup, 'div', id='webid')
        # result = _get_from_element(
        #     result, 'collocation', soup, 'div', id='colid')
        # result = _get_from_element(
        #     result, 'synonym', soup, 'div', id='synoid')
        # result = _get_from_element(
        #     result, 'antonym', soup, 'div', id='antoid')
        # result = _get_from_element(
        #     result, 'samples', soup, 'div', id='sentenceCon')
        return self.cache_this(result)
        # except Exception as e:
        #     showInfo(str(e))
        #     return {}

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)

    @export(u'美式音标', 1)
    def fld_phonetic_us(self):
        return self._get_field('phonitic_us')

    @export(u'英式音标', 2)
    def fld_phonetic_uk(self):
        return self._get_field('phonitic_uk')

    @export(u'词语时态', 3)
    def fld_participle(self):
        return self._get_field('participle')

    @export(u'释义', 4)
    def fld_definition(self):
        return self._get_field('def')

    # @export(u'权威英汉双解', 5)
    # def fld_advanced_ec(self):
    #     return self._get_field('advanced_ec')

    # @export(u'英汉', 6)
    # def fld_ec(self):
    #     return self._get_field('ec')

    # @export(u'英英', 7)
    # def fld_ee(self):
    #     return self._get_field('ee')

    # @export(u'网络释义', 8)
    # def fld_web_definition(self):
    #     return self._get_field('web_definition')

    # @export(u'搭配', 9)
    # def fld_collocation(self):
    #     return self._get_field('collocation')

    # @export(u'同义词', 10)
    # def fld_synonym(self):
    #     return self._get_field('synonym')

    # @export(u'反义词', 11)
    # def fld_antonym(self):
    #     return self._get_field('antonym')

    # @export(u'例句', 12)
    # def fld_samples(self):
    #     return self._get_field('samples')
