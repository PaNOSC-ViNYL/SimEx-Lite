#!/bin/bash

# comment symbol
cs="#"
# source code suffix
sc_suffix=".py"
year="2021"
project="SimEx-Lite"
license="GNU General Public License v3"
authors="Juncheng E"
contact="Juncheng E"
email="juncheng.e@xfel.eu"
url="http://www.gnu.org/licenses"

echo "Preview:"
echo ""

cat <<EOF | tee copyright.txt.tmp
$cs Copyright (C) $year $authors
$cs Contact: $contact <$email>
$cs This file is part of $project which is released under $license.
$cs See file LICENSE or go to <$url> for full license details.
EOF

if [[ "$2" != "add" || -z "$1" ]]
then
    echo "This is a dryrun. To add this copyright header to files in this folder:"
    echo "$0 PATH add"
    echo "example: $0 ./ add"
    echo ""
fi

if [[ -n $1 ]]
then
    echo "$0 $1 add"
    for i in $1/*${sc_suffix} # or whatever other pattern...
    do
        if ! grep -q Copyright $i
        then
            if [[ "$2" == "add" ]]
            then
                echo Added copyright to $i
                cat copyright.txt.tmp $i >$i.new && mv $i.new $i
            else
                echo will add copyright to $i
            fi
        fi
    done
fi

rm copyright.txt.tmp