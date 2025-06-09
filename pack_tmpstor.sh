#!/usr/bin/env bash
if [ "$1" != "" ]; then
    LM="$1"
else
    LM=`date --date "last month" +%Y-%m`
fi
cd "`dirname $0`"
a="tmpstor_${LM}.tbz"
num=`ls tmpstor/.${LM}-*.zip 2> /dev/null | wc -l`
if [ $num -gt 0 -a ! -e "$a" ] ; then
    echo $a
    ls -l tmpstor/.${LM}-*.zip
    tar -cvjpf "$a" tmpstor/.${LM}-*.zip && rm tmpstor/.${LM}-*.zip
fi
