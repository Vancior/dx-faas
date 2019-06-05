while inotifywait -q -r ./edge/* ./web/* ./sdk/*; do
    # rsync -arvz ./ ivic@192.168.106.164:/home/hujuntao/gitrepo/dx-proto --delete
    rsync -arvz ./ ivic@192.168.106.164:/home/ivic/deploy/dx-proto --delete
done
