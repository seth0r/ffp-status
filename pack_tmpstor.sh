#!/usr/bin/env bash
LM=`date --date "last month" +%Y-%m`
cd "`dirname $0`"
for d in tmpstor/.${LM}-*; do
    a="tmpstor_`echo $d | cut -d. -f2`.tbz"
    if [ -d "$d" -a ! -e "$a" ] ; then
        tar -cjpf "$a" "$d" && rm -r "$d"
    fi
done
