# coding=utf-8
#
# Copyright 2014 Sascha Schirra
#
# This file is part of Ropper.
#
# Ropper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ropper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
from ropper.common.error import *
from ropper.common.utils import isHex
from ropper.common.coloredstring import cstr
import sys



class Options(object):



    def __init__(self, argv):
        super(Options, self).__init__()

        self.__argv = argv
        self.__args = None
        self.__parser = self._createArgParser()
        self._analyseArguments()
        self.__callbacks = []

    def _createArgParser(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
description="""You can use ropper to display information about binary files in different file formats
    and you can search for gadgets to build rop chains for different architectures

supported filetypes:
  ELF
  PE
  Mach-O
  Raw

supported architectures:
  x86 [x86]
  x86_64 [x86_64]
  MIPS [MIPS, MIPS64]
  ARM/Thumb [ARM, ARMTHUMB]
  ARM64 [ARM64]
  PowerPC [PPC, PPC64]

available rop chain generators:
  execve (execve[=<cmd>], default /bin/sh) [Linux x86, x86_64]
  mprotect  (mprotect=<address>:<size>) [Linux x86, x86_64]
  virtualprotect (virtualprotect=<address iat vp>:<size>) [Windows x86]
""",
epilog="""example uses:
  [Generic]
  ropper.py
  ropper.py --file /bin/ls --console

  [Informations]
  ropper.py --file /bin/ls --info
  ropper.py --file /bin/ls --imports
  ropper.py --file /bin/ls --sections
  ropper.py --file /bin/ls --segments
  ropper.py --file /bin/ls --set nx
  ropper.py --file /bin/ls --unset nx

  [Gadgets]
  ropper.py --file /bin/ls --inst-count 5
  ropper.py --file /bin/ls --search "sub eax" --badbytes 000a0d
  ropper.py --file /bin/ls --search "sub eax" --detail
  ropper.py --file /bin/ls --filter "sub eax"
  ropper.py --file /bin/ls --inst-count 5 --filter "sub eax"
  ropper.py --file /bin/ls --opcode ffe4
  ropper.py --file /bin/ls --opcode ffe?
  ropper.py --file /bin/ls --opcode ??e4
  ropper.py --file /bin/ls --detailed
  ropper.py --file /bin/ls --ppr --nocolor
  ropper.py --file /bin/ls --jmp esp,eax
  ropper.py --file /bin/ls --type jop
  ropper.py --file /bin/ls --chain execve=/bin/sh
  ropper.py --file /bin/ls --chain execve=/bin/sh --badbytes 000a0d
  ropper.py --file /bin/ls --chain mprotect=0xbfdff000:0x21000

  [Search]
  ?\t\tany character
  %\t\tany string

  Example:

  ropper.py --file /bin/ls --search "mov e?x"
  0x000067f1: mov edx, dword ptr [ebp + 0x14]; mov dword ptr [esp], edx; call eax
  0x00006d03: mov eax, esi; pop ebx; pop esi; pop edi; pop ebp; ret ;
  0x00006d6f: mov ebx, esi; mov esi, dword ptr [esp + 0x18]; add esp, 0x1c; ret ;
  0x000076f8: mov eax, dword ptr [eax]; mov byte ptr [eax + edx], 0; add esp, 0x18; pop ebx; ret ;

  ropper.py --file /bin/ls --search "mov [%], edx"
  0x000067ed: mov dword ptr [esp + 4], edx; mov edx, dword ptr [ebp + 0x14]; mov dword ptr [esp], edx; call eax;
  0x00006f4e: mov dword ptr [ecx + 0x14], edx; add esp, 0x2c; pop ebx; pop esi; pop edi; pop ebp; ret ;
  0x000084b8: mov dword ptr [eax], edx; ret ;
  0x00008d9b: mov dword ptr [eax], edx; add esp, 0x18; pop ebx; ret ;

  ropper.py --file /bin/ls --search "mov [%], edx" --quality 1
  0x000084b8: mov dword ptr [eax], edx; ret ;
  \n""")


        parser.add_argument(
            '-v', '--version', help="Print version", action='store_true')
        parser.add_argument(
            '--console', help='Starts interactive commandline', action='store_true')
        parser.add_argument(
            '-f', '--file', metavar="<file>", help='The file to load')
        parser.add_argument(
            '-r', '--raw', help='Loads the file as raw file', action='store_true')
        parser.add_argument(
             '--db', metavar="<dbfile>", help='The dbfile to load')
        parser.add_argument(
            '-a', '--arch', metavar="<arch>", help='The architecture of the loaded file')
        parser.add_argument(
            '--section', help='The data of the this section should be printed', metavar='<section>')
        parser.add_argument(
            '--string', help='Looks for the string <string> in all data sections', metavar='<string>',nargs='?', const='[ -~]{2}[ -~]*')
        parser.add_argument(
            '--hex', help='Prints the selected sections in a hex format', action='store_true')
        parser.add_argument(
            '--asm', help='A string to assemble', nargs='+')
        parser.add_argument(
            '--disasm', help='A string to disassemble')
        parser.add_argument(
            '--disassemble-address', help='Disassembles instruction at address <address> (0x12345678:L3). The count of instructions to disassemble can be specified (0x....:L...)', metavar='<address:length>')
        parser.add_argument(
            '-i', '--info', help='Shows file header [ELF/PE/Mach-O]', action='store_true')
        parser.add_argument('-e', help='Shows EntryPoint', action='store_true')
        parser.add_argument('--imagebase', help='Shows ImageBase [ELF/PE/Mach-O]', action='store_true')
        parser.add_argument(
            '-c', '--dllcharacteristics',help='Shows DllCharacteristics [PE]', action='store_true')
        parser.add_argument(
            '-s', '--sections', help='Shows file sections [ELF/PE/Mach-O]', action='store_true')
        parser.add_argument(
            '-S', '--segments', help='Shows file segments [ELF/Mach-O]', action='store_true')
        #parser.add_argument(
        #    '--checksec', help='Shows the security mechanisms used in the file [ELF/PE/Mach-O]', action='store_true')
        parser.add_argument(
            '--imports', help='Shows imports [ELF/PE]', action='store_true')
        parser.add_argument(
            '--symbols', help='Shows symbols [ELF]', action='store_true')
        parser.add_argument(
            '--set', help='Sets options. Available options: aslr nx', metavar='<option>')
        parser.add_argument(
            '--unset', help='Unsets options. Available options: aslr nx', metavar='<option>')
        parser.add_argument('-I', metavar='<imagebase>', help='Uses this imagebase for gadgets')
        parser.add_argument(
            '-p', '--ppr', help='Searches for \'pop reg; pop reg; ret\' instructions [only x86/x86_64]', action='store_true')
        parser.add_argument(
            '-j', '--jmp', help='Searches for \'jmp reg\' instructions (-j reg[,reg...]) [only x86/x86_64]', metavar='<reg>')
        parser.add_argument(
            '--stack-pivot', help='Prints all stack pivot gadgets',action='store_true')
        parser.add_argument(
            '--inst-count', help='Specifies the max count of instructions in a gadget (default: 5)', metavar='<n bytes>', type=int, default=5)
        parser.add_argument(
            '--search', help='Searches for gadgets', metavar='<regex>')
        parser.add_argument(
            '--quality', help='The quality for gadgets which are found by search (1 = best)', metavar='<quality>', type=int)
        parser.add_argument(
            '--filter', help='Filters gadgets', metavar='<regex>')
        parser.add_argument(
            '--opcode', help='Searchs for opcodes (e.g. ffe4 or ffe? or ff??)', metavar='<opcode>')
        parser.add_argument(
            '--instructions', help='Searchs for instructions (e.g. "jmp esp", "pop eax; ret")', metavar='<instructions>')
        parser.add_argument(
            '--type', help='Sets the type of gadgets [rop, jop, sys, all] (default: all)', metavar='<type>', default='all')
        parser.add_argument(
            '--detailed', help='Prints gadgets more detailed', action='store_true')
        parser.add_argument(
            '--all', help='Does not remove duplicate gadgets', action='store_true')
        parser.add_argument(
            '--chain', help='Generates a ropchain [generator=parameter]', metavar='<generator>')
        parser.add_argument(
            '-b', '--badbytes', help='Set bytes which should not contains in gadgets', metavar='<badbytes>', default='')
        parser.add_argument(
            '--nocolor', help='Disables colored output', action='store_true')
        return parser

    def _analyseArguments(self):

        if len(self.__argv) == 0 or (len(self.__argv) == 1 and self.__argv[0] == '--nocolor'):
            self.__argv.append('--console')
        self.__args = self.__parser.parse_args(self.__argv)

        self.nocolor = self.__args.nocolor and not self.isWindows()

        if not self.__args.asm and not self.disasm and not self.__args.console and not self.__args.file and not self.__args.version:
            self.__missingArgument('[-f|--file]')

        if self.__args.I:
            if not isHex(self.__args.I):
                raise ArgumentError('Imagebase should be in hex (0x.....)')
            else:
                self.__args.I = int(self.__args.I, 16)


    def __missingArgument(self, arg):
        raise ArgumentError('Missing argument: %s' % arg)

    def __getattr__(self, key):
        if key == 'color':
            key = 'nocolor'
        if key.startswith('_'):
            return super(Options, self).__getattr__(key)
        else:
            return vars(self.__args)[key]

    def isWindows(self):
      return sys.platform.startswith('win')

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super(Options, self).__setattr__(key, value)
        else:
            if key == 'nocolor':
              cstr.COLOR = not value
            vars(self.__args)[key] = value

    def setOption(self, key, value):
        if key in VALID_OPTIONS:
            old = self.getOption(key)
            result = VALID_OPTIONS[key](self, value)
            self.notifyOptionChanged(key, old, value)
            if result:
                return result[1]

            else:
              raise RopperError('Invalid value for option %s: %s' %(key, value))
        else:
            raise RopperError('Invalid option')

    def getOption(self, key):
        if key in VALID_OPTIONS:
            return self.__getattr__(key)
        else:
            raise RopperError('Invalid option: %s ' % key)

    def addOptionChangedCallback(self, func):
        self.__callbacks.append(func)

    def removeOptionChangedCallback(self, func):
        del self.__callbacks[self.__callbacks.index(func)]

    def notifyOptionChanged(self, option, old, new):
        for cb in self.__callbacks:
            cb(option, old, new)

    def _setAll(self, value):
        if value.lower() in ('on', 'off'):
            self.all = bool(value == 'on')
            return  (True,True)
        return False

    def _setInstCount(self, value):
        if value.isdigit():
            self.inst_count = int(value)
            return (True,True)
        return False

    def _setBadbytes(self, value):
        if len(value) == 0 or isHex('0x'+value):
            self.badbytes = value
            return  (True,True)
        return False

    def _setDetailed(self, value):
        if value.lower() in ('on', 'off'):
            self.detailed = bool(value == 'on')
            return (True, False)
        return False

    def _setType(self, value):
        if value in ['rop','jop','sys','all']:
            self.type = value
            return  (True,True)
        return False

    def _setColor(self, value):
        if value.lower() in ('on', 'off'):
            self.nocolor = bool(value == 'off')
            return (True,False)
        return False

VALID_OPTIONS = {'all' : Options._setAll,
                     'inst_count' : Options._setInstCount,
                     'badbytes' : Options._setBadbytes,
                     'detailed' : Options._setDetailed,
                     'type' : Options._setType,
                     'color' : Options._setColor}
