""""
Stop method for BatchProcessor class.
This is a temporary file that will be used to add the missing stop method.
""""

def stop(self, wait: bool = True, timeout: float = 10.0):
    """Stop batch processing (alias for cancel_batch that accepts wait and timeout params)."""
    logger.info(f"Stopping batch processor with wait={wait}, timeout={timeout}")
    
    # Call the existing cancel_batch method
    self.cancel_batch()
    
    # If wait is requested, wait for threads to exit
    if wait and self.worker_threads:
        # Set appropriate timeouts
        thread_timeout = timeout / len(self.worker_threads) if len(self.worker_threads) > 0 else timeout
        
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=thread_timeout)
                
        # Clear thread list after waiting
        self.worker_threads = []
    
    return
