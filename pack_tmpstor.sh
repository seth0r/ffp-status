#!/usr/bin/env bash
LM=`date --date "last month" +%Y-%m`
cd "`dirname $0`"
a="tmpstor_${LM}.tbz"
num=`ls tmpstor/.${LM}-*.zip 2> /dev/null | wc -l`
if [ $num -gt 0 -a ! -e "$a" ] ; then
    echo $a
    ls -l tmpstor/.${LM}-*.zip
    tar -cjpf "$a" tmpstor/.${LM}-*.zip && rm tmpstor/.${LM}-*.zip
fi
