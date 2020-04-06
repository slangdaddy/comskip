#!/bin/bash

WORKDIR=/work
INPUTDIR=/input
OUTPUTDIR=/output
CONFDIR=/config

# Start program
if [ -n "${DEBUG}" ]; then
	echo "Some debugging information:"
	echo "Environment:"
	env
	echo "Current user:"
	whoami
	echo "Setting bash verbose mode.."
	set -x
fi
if [ ! -f "${CONFDIR}/comskip.ini" ]; then
	echo "Copying default comskip.ini to config dir.."
	cp /opt/Comskip/comskip.ini ${CONFDIR}/comskip.ini
fi
while true; do
	echo "Looping over items in '${INPUTDIR}'"
	for i in ${INPUTDIR}/*; do
		# TODO: improve VDR-style folder structure / naming compatibility
		echo "Processing '${i}'.."
		item_basename=$(basename $i)
		item_basename=${item_basename%.*}
		item_ext=${i##*.}
		item=${i}
		item_matroska=${item_basename}.mkv

		# TODO: allow more flexibility
		if [[ -d ${item} && "${item_ext}" == "rec" ]]; then
			echo "Found recording directory."

			if [ -f "${OUTPUTDIR}/${item_basename}.mkv" ]; then
				echo "Output file already exists.."
				continue
			fi

			echo "Concatenating .ts files.."
			cat ${item}/*.ts > ${WORKDIR}/${item_basename}.ts
			item=${WORKDIR}/${item_basename}.ts

			echo "Converting transport stream to Matroska.."
			ffmpeg -i ${item} -map 0 -c:v libx264 -c:a copy -c:s copy -nostdin -y ${WORKDIR}/${item_matroska}
			if [ "$?" -ne "0" ]; then
				echo "Error running ffmpeg.."
				continue
			fi

			echo "Calling comchap.."
			/opt/comchap/comchap --keep-edl --comskip=/opt/Comskip/comskip --comskip-ini=/config/comskip.ini ${WORKDIR}/${item_matroska}
			if [ "$?" -ne "0" ]; then
				echo "Error running comchamp.."
				continue
			fi

			echo "Moving result to output directory.."
			mv ${WORKDIR}/${item_basename}.mkv ${WORKDIR}/${item_basename}.edl ${OUTPUTDIR}/

			# TODO: check if output file is at least 90% in size of input file
			if [ -f "${OUTPUTDIR}/${item_basename}.mkv" ]; then
				echo "Cleaning up.."
				rm -rvf ${WORKDIR}/${item_basename}.ts ${i}
			else
				echo "Something went wrong. Generated file not found where expected ('${OUTPUTDIR}/${item_basename}.mkv')"
				continue
			fi
		fi
	done

	echo "Sleeping for next iteration.."
	sleep 30s
done
