#!/usr/bin/env python
'''
Batch process packages by running accession.py and makepbcore.py
roadmap:
use extract_metadata() to analyze filmo csv and return oe_list
check oe_list against input dir. is everything there?
loop through oe list - but use order.py to detect parent.
add option to accession.py to get starting filmo reference number.
Run batchaccession processes, filling in the ref no in the pbcore AND filmo.
The outcome will be:
* Packages are accessioned
* Filmographic records can be ingested to DB TEXTWORKS
* Technical records can be ingested to DB TEXTWORKS
* Skeleton accession record can be also be made available.

how:
customise get_metadata - it should produce a dict that says:
current oe#=aaa1001, hugo rushes 2

and then the user confirms all that.

'''
import argparse
import sys
import os
import ififuncs
import accession
import copyit
import order

def initial_check(args, accession_digits, oe_list, reference_number):
    '''
    Tells the user which packages will be accessioned and what their accession
    numbers will be.
    '''
    to_accession = {}
    wont_accession = []
    accession = 'af' + str(accession_digits)
    ref = reference_number
    reference_digits = int(ref[2:])
    for root, _, _ in os.walk(args.input):
        if os.path.basename(root)[:2] == 'oe':
            if len(os.path.basename(root)[2:]) == 4:
                if copyit.check_for_sip(root) is None:
                    wont_accession.append(root)
                    #print '%s looks like it is not a fully formed SIP. Perhaps loopline_repackage.py should proccess it?' % root
                else:
                    # this is just batchaccessioning if no csv is supplied
                    if len(oe_list) == 0:
                        to_accession[root] = 'aaa' + str(accession_digits)
                        accession_digits += 1
                    else:
                        # this should kick in if a csv is supplied.
                        # only the items in the csv will pass forward for accessioning.
                        # the parent OE should also be in here.
                        # I just realised - perhaps the removal of converteds is not necessary.
                        # Maybe, just maybe - we should have a policy that states:
                        # the concat and its parent is what will be accessioned.
                        # ask aoife if she only concatted from the best master.
                        # THIS COULD SOLVE A LOT OF ISSUES. THE SCRIPT FOLLOWS THE POLICY.
                        if os.path.basename(root) in oe_list:
                            to_accession[os.path.join(os.path.dirname(root), order.main(root))] = ['aaa' + str(accession_digits), ref[:2] + str(reference_digits)]
                            accession_digits += 1
                            to_accession[root] = ['aaa' + str(accession_digits), ref[:2] + str(reference_digits)]
                            reference_digits +=1
                            accession_digits +=1
    print to_accession
    sys.exit()
    for fails in wont_accession:
            print '%s looks like it is not a fully formed SIP. Perhaps loopline_repackage.py should proccess it?' % fails
    for success in sorted(to_accession.keys()):
        print '%s will be accessioned as %s' %  (success, to_accession[success])
    return to_accession

def parse_args(args_):
    '''
    Parse command line arguments.
    '''
    parser = argparse.ArgumentParser(
        description='Batch process packages by running accession.py and makepbcore.py'
        ' Written by Kieran O\'Leary.'
    )
    parser.add_argument(
        'input', help='Input directory'
    )
    parser.add_argument(
        '-start_number',
        help='Enter the Accession number for the first package. The script will increment by one for each subsequent package.'
    )
    parser.add_argument(
        '-csv',
        help='Enter the path to the Filmographic CSV'
    )
    parser.add_argument(
        '-reference',
        help='Enter the starting Filmographic reference number for the representation.'
    )
    parsed_args = parser.parse_args(args_)
    return parsed_args

def get_afNNNN_number(number):
    '''
    This check is not sustainable, will have to be made more flexible!
    '''
    if len(number) == 7:
        if number[:3] == 'af1':
            return number
    else:
        number = ififuncs.get_reference_number()
        return number
def get_number(args):
    '''
    Figure out the first accession number and how to increment per package.
    '''
    if args.start_number:
        if args.start_number[:3] != 'aaa':
            print 'First three characters must be \'aaa\' and last four characters must be four digits'
            accession_number = ififuncs.get_accession_number()
        elif len(args.start_number[3:]) != 4:
            accession_number = ififuncs.get_accession_number()
            print 'First three characters must be \'aaa\' and last four characters must be four digits'
        elif not args.start_number[3:].isdigit():
            accession_number = ififuncs.get_accession_number()
            print 'First three characters must be \'aaa\' and last four characters must be four digits'
        else:
            accession_number = args.start_number
    else:
        accession_number = ififuncs.get_accession_number()
    return accession_number

def main(args_):
    '''
    Batch process packages by running accession.py and makepbcore.py
    '''
    args = parse_args(args_)
    oe_list = []
    if args.csv:
        for i in ififuncs.extract_metadata(args.csv):
            oe_number = i['Object Entry'].lower()
            transformed_oe = oe_number[:2] + oe_number[3:]
            oe_list.append(transformed_oe)
    if args.reference:
        reference_number = get_afNNNN_number(args.reference)
    else:
        reference_number = ififuncs.get_reference_number()
    user = ififuncs.get_user()
    accession_number = get_number(args)
    accession_digits = int(accession_number[3:])
    to_accession = initial_check(args, accession_digits, oe_list, reference_number)
    proceed = ififuncs.ask_yes_no(
        'Do you want to proceed?'
    )
    if proceed == 'Y':
        for package in sorted(to_accession.keys()):
            accession.main([
                package, '-user', user,
                '-p', '-f', '-number',
                to_accession[package]
            ])

if __name__ == '__main__':
    main(sys.argv[1:])
