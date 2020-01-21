#!/usr/bin/env bash

timestamp() {
    date +"%Y-%m-%d_%H-%M-%S"
}

# change directory to add-on directory.
none_type_values=$1
bool_type_values=$2
add_on_directory='add-on'
merge_script_report='merge_report.txt'
user_input_file='user-input.yaml'
add_on_manifest='add_on_manifest.yaml'

echo "Merge script started." >> $merge_script_report

# create directories if they don't exist
mkdir -p templates
mkdir -p parameters
mkdir -p policies

# create duplicate copy of all existing assets
mkdir -p original
rsync -av * original
rm -rf original/original
ls -ltr original

echo "Check python version"
which pip && pip --version
which python3 && python3 --version

#create add-on-manifests directory
add_on_manifest_directory='add-on-manifests'
mkdir -p $add_on_manifest_directory

# Check if add-on directory exist in the configuration
if [ -d $add_on_directory ];
then
    # Iterate through all the zip files in alphabetical order and unzip them all
    ls $add_on_directory
    # Check of $add_on_directory" is empty
    if [ "$(ls $add_on_directory)" ]; then
        echo "$add_on_directory directory is not Empty"
        ls  | grep "zip$" | sort

        # Processing zip files
        for x in `ls  $add_on_directory | grep "zip$" | sort`;
        do
            # create new directory for each zip
            sub_add_on_dir=`echo $x | cut -d. -f1`
            echo "Creating directory file" $add_on_directory/$sub_add_on_dir
            echo "$ mkdir -p $add_on_directory/$sub_add_on_dir"
            mkdir -p $add_on_directory/$sub_add_on_dir

            # find all the zip files and unzip

            echo "Unzipping file:" $add_on_directory/$x >> $merge_script_report
            echo "$ unzip -o $add_on_directory/$x -d $add_on_directory/$sub_add_on_dir"
            unzip -o $add_on_directory/$x -d $add_on_directory/$sub_add_on_dir

            # track processed zip file after running required tasks
            echo "Finished unzipping $add_on_directory/$x." >> $merge_script_report
            echo "-----------------------------------------------------------------------------" >> $merge_script_report
        done
    else
        echo "$add_on_directory directory is Empty"
    fi
else
    echo "Could not find 'add-on directory'"
fi

# Move add-on manifest files to the add-on folder
# Check if add-on directory exist in the configuration
if [ -d $add_on_directory ];
then
    # Iterate through all the directories in alphabetical order and sync the files.
    ls $add_on_directory
    # Check of $add_on_directory" is empty
    if [ "$(ls $add_on_directory)" ]; then
        echo "$add_on_directory directory is not Empty"
        ls  | grep "zip$" | sort

        # Processing all the directories in the 'add-on' directory
        counter=0
        for y in `ls -d $add_on_directory/* | grep -v 'zip$' | sort`;
        do
            counter=$((counter+1))
            timestamp >> $merge_script_report

            # Update files with user input
            echo "Updating files based on user's input"
            echo "python3 find_replace.py $y/$user_input_file $y $bool_type_values $none_type_values"
            python3 find_replace.py $y/$user_input_file $y $bool_type_values $none_type_values
            # Check python script exit code
            if [ $? -ne 0 ]
            then
              echo "Find-Replace with user input failed."
              exit 1
            fi

            echo "Processing $y directory"

             # Copy add-on manifest to a manifest directory
            echo "Copying $add_on_manifest to $add_on_manifest_directory directory as add_on_manifest_$counter.yaml" >> $merge_script_report
            # copying the manifest from the add-on directory to the separate directory for processing.
            echo "cp $y/$add_on_manifest $add_on_manifest_directory/"add_on_manifest_$counter.yaml""
            cp $y/$add_on_manifest $add_on_manifest_directory/"add_on_manifest_$counter.yaml"
            echo "-----------------------------------------------------------------------------" >> $merge_script_report
        done
    else
        echo "$add_on_directory directory is Empty"
    fi
else
    echo "Could not find 'add-on directory'"
fi

# Merge master manifest file with the add-on manifest files
# iterate through the add-on manifest files
if [ -d $add_on_manifest_directory ];
then
    # Iterate through all the add-on manifest files in alphabetical order
    if [ "$(ls $add_on_manifest_directory)" ];
    then
        # Check if add_on_manifest_directory exist
        echo "$add_on_manifest_directory directory is not Empty"
        dir_name_length=`echo $add_on_manifest_directory | wc -m`
        # the length sorts following x1 x10 x11 x2 x3 to x1 x2 x3 x10 x11
        for x in `ls $add_on_manifest_directory | sort -nk1.$(($dir_name_length))`;
        do
            timestamp >> $merge_script_report
            echo $add_on_manifest_directory/$x
            if [ "$(grep '{{' $add_on_manifest_directory/$x)" ];
            then
                echo "Found jinja pattern '{{ <string> }}' in file: `grep '{{' $add_on_manifest_directory/* | cut -f1 -d: | uniq`"
                echo "Please check user-input.yaml to make sure all jinja keys are replaced with user value."
                exit 1
            else
                echo "Processing file:" $add_on_manifest_directory/$x >> $merge_script_report
                echo "python3 merge_manifest.py manifest.yaml $add_on_manifest_directory/$x manifest.yaml"
                python3 merge_manifest.py manifest.yaml $add_on_manifest_directory/$x manifest.yaml
                # Check python script exit code
                if [ $? -ne 0 ]
                then
                  echo "Merging manifest files failed."
                  exit 1
                fi
                # track processed manifest file after merging the manifests
                echo "Finished merging manifest file: $add_on_manifest_directory/$x" >> $merge_script_report
                echo "-----------------------------------------------------------------------------" >> $merge_script_report
            fi
        done
    else
        echo "$add_on_manifest_directory directory is Empty"
    fi
else
    echo "'add-on-manifest directory' not found, nothing to merge."
fi

# Check if add-on directory exist in the configuration
if [ -d $add_on_directory ];
then
    # Iterate through all the directories in alphabetical order and sync the files.
    ls $add_on_directory
    # Check of $add_on_directory" is empty
    if [ "$(ls $add_on_directory)" ];
    then
        echo "$add_on_directory directory is not Empty"
        ls  | grep "zip$" | sort

        # Processing all the directories in the 'add-on' directory
        for y in `ls -d $add_on_directory/* | grep -v 'zip$' | sort`;
        do
            timestamp >> $merge_script_report
            echo "Copying only new files to the existing templates, parameters or policies directory"
            if [ -d $y/templates ];
            then
                echo "rsync  --ignore-existing --verbose --recursive $y/templates/* templates"
                rsync  --ignore-existing --verbose --recursive $y/templates/* templates
                echo "Templates synced." >> $merge_script_report
            else
                echo "'templates' directory not found in $y."
                echo "'templates' directory not found in $y." >> $merge_script_report
            fi
            if [ -d $y/parameters ];
            then
                echo "rsync  --ignore-existing --verbose --recursive $y/parameters/* parameters"
                rsync  --ignore-existing --verbose --recursive $y/parameters/* parameters
                echo "Parameters synced." >> $merge_script_report
            else
                echo "'parameters' directory not found in $y."
                echo "'parameters' directory not found in $y." >> $merge_script_report
            fi
            if [ -d $y/policies ];
            then
                echo "rsync  --ignore-existing --verbose --recursive $y/policies/* policies"
                rsync  --ignore-existing --verbose --recursive $y/policies/* policies
                echo "Policies synced." >> $merge_script_report
            else
                echo "'policies' directory not found in $y."
                echo "'policies' directory not found in $y." >> $merge_script_report
            fi
            echo "-----------------------------------------------------------------------------" >> $merge_script_report
        done
    else
        echo "$add_on_directory directory is Empty"
    fi
else
    echo "Could not find 'add-on directory'"
fi

# Check if add-on directory exist in the configuration
if [ -d $add_on_directory ];
then
    # Iterate through all the directories in alphabetical order and sync the files.
    ls $add_on_directory
    # Check of $add_on_directory" is empty
    if [ "$(ls $add_on_directory)" ];
    then
        echo "$add_on_directory directory is not Empty"
        ls  | grep "zip$" | sort

        # Processing all the directories in the 'add-on' directory
        for y in `ls -d $add_on_directory/* | grep -v 'zip$' | sort`;
        do
            timestamp >> $merge_script_report
            echo "-----------------------------------------------------------------------------" >> $merge_script_report
        done
    else
        echo "$add_on_directory directory is Empty"
    fi
else
    echo "Could not find 'add-on directory'"
fi

if [ -a add_on_avm_files.json ]; then
  # iterate through avm template and parameter file and merge them
  echo "Merging AVM template and parameter files started." >> $merge_script_report
  echo "python3 merge_baseline_template_parameter.py info master_avm_files.json add_on_avm_files.json"
  python3 merge_baseline_template_parameter.py info master_avm_files.json add_on_avm_files.json
  #Check python script exit code
  if [ $? -ne 0 ]
  then
    echo "Merging AVM template and parameter files failed." >> $merge_script_report
    echo "Merging AVM template and parameter files failed."
    exit 1
  else
    echo "Merging AVM template and parameter files finished." >> $merge_script_report
  fi
else
    echo "No Add-On AVM templates to merge"
fi
echo "-----------------------------------------------------------------------------" >> $merge_script_report
echo "Merge script finished."
echo "Merge script finished." >> $merge_script_report
