最高裁判例蒐集スクリプト
========================

概要
~~~~
`最高裁の判例検索 <http://www.courts.go.jp/search/jhsp0010?action_id=first&hanreiSrchKbn=02>`_ の結果(html)から判例をなるべく穏便に取得するためのスクリプトです。
30秒のリクエストディレイをはさみながら、 ``<HanreiData><Hanrei>...</Hanrei>...</HanreiData>`` というようなXMLを生成していきます。

動かし方
~~~~~~~~
事前に必要なのは以下になります。

* Python2.7およびvirtualenv
* pdftotext

判例をダウンロードするには、まず `検索システム <http://www.courts.go.jp/search/jhsp0010?action_id=first&hanreiSrchKbn=02>`_ の事件リストページを収集します。
このとき、ファイル名の形式を :code:`<any text>_<category>_<any text>.html` のようにすると、 https://github.com/drowse314-dev-ymat/hanrei_abstract_extractor との連携に役立ちます。

.. code-block:: txt

    minji_searches
    ├── minji_ju_page1.html
    ├── minji_ju_page2.html
    └── minji_ju_page3.html

収集した検索結果リストから、個々の判例のデータを取得します。

.. code-block:: sh

    virtualenv-2.7 venv # 名前はなんでも
    source venv/bin/activate
    pip install -r requirements.txt
    python run.py /path/to/minji_searches

判例は検索結果リストのhtmlファイル単位でダウンロードされ、ひとつのリストにリンクが含まれる判例群から
ひとつのXMLファイルが生成されます。
XMLファイルは、 `hanreidata </hanreidata>`_ 内に順次蓄積されます。
ファイル名は ``<file name>.html`` に対して ``<file name>.xml`` となります。

検索結果リストは、複数のディレクトリから参照することができます。
その場合は単純に、 ``python run.py list_dir1 [list_dir2 list_dir3 ...]`` とします。

英語判例の取得
~~~~~~~~~~~~~~
`英語版の判例検索 <http://www.courts.go.jp/english/judgments/index.html>`_ にも(無理やり)対応しています。
以下のオプションを指定することで、 日本語版とほぼ同様の処理になります。

.. code-block:: sh

    python run.py english_list_dir --en_list

英語版では様々なデータ抜けが発生し、すぐに異常終了してしまうかもしれません。
その場合は、ブランチを ``interactive_fallback`` に切替えると、エラーが送出される前に抜け属性をスキップするか、
または補完するかどうか等を対話的に選択することができます。
``--en_fill_empty`` オプションを付加すると、この選択を自動化することができます。
オプションの詳細については、 ``python run.py --help`` を参照して下さい。

ダウンロードの中断
~~~~~~~~~~~~~~~~~~
ダウンロード中に異常終了した場合、あるいは割り込みによって終了した場合、同じリストについてまたダウンロードを始めると、
ダウンロード済の判例をキャッシュとして扱い、途中から再開することができます。
このとき、キャッシュの有無は `hanreidata </hanreidata>`_ 内に蓄積されたXMLファイルの名称によって判断されるので、異常終了によって
空のXMLファイル等が生成された場合は注意して下さい。
