class CombinedProgressWatcher():
    """
    Simple class to convert a list of progress percentage into one scalar value.
    It's basically just calculating the mathematical average of all percentages
    for the list of downloads passed in.
    The list can be updated afterwards when a reference is retained in the calling code.
    In that case, CombinedProgressWatcher.list_updated must be used to fix progress callbacks
    and cached percentages to match the new content of the list.
    """

    def __init__(self, progress_func, download_list=[]):
        self.callback_progress = progress_func
        self.download_list = download_list
        self.download_progress = {}
        self.current_progress = 0
        # make sure it can be used directly
        self.list_updated()

    @property
    def num_downloads(self):
        return len(self.download_list)

    @property
    def progress_list(self):
        return self.download_progress.values()

    def list_updated(self):
        """
        Should be called whenever the passed in download list changes in any way.
        New download instances will have the progress callback assigned and instances
        which were removed will also have the progress callback removed again.
        """
        for download in self.download_list:
            if self.download_progress.get(download, None) is None:
                self.download_progress[download] = 0
                self.bind_progress_callback(download)

        for removed in [*self.download_progress.keys()]:
            if removed not in self.download_list:
                del self.download_progress[removed]
                removed.on_progress(None)

        self.update_progress()

    def update_progress(self, download=None, progress=0):
        """
        rough overall progress estimate. Basically the sum of all percentages / num files
        this is rough because it does not consider file sizes at all,
        so percentages will update very fast in the beginning when small files are downloaded, then slow down
        """
        if download:
            self.download_progress[download] = progress

        if self.num_downloads:
            new_progress = int(sum(self.progress_list) / self.num_downloads)
        else:
            new_progress = 0

        if new_progress != self.current_progress:
            self.callback_progress(new_progress)
            self.current_progress = new_progress

    def bind_progress_callback(self, download):
        download.on_progress(lambda progress: self.update_progress(download, progress))
