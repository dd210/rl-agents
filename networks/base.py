
import numpy as np
import tensorflow as tf


class NetworkBase(object):

    def __init__(self):
        self.inp, self.out, self.loss = self._build_network()

    def _build_network(self):
        raise NotImplementedError

    def _iterate_minibatches(self, x, y, batch_size=32, shuffle=True):
        """Iterator over dataset."""
        l = x.shape[0]
        indices = np.arange(l)
        if shuffle:
            np.random.shuffle(indices)
        for start_idx in range(0, l, batch_size):
            end_idx = min(start_idx + batch_size, l)
            if shuffle:
                excerpt = indices[start_idx:end_idx]
            else:
                excerpt = slice(start_idx, end_idx)
            yield x[excerpt], y[excerpt]

    def train(self, sess, x, y, n_epochs=1, batch_size=32, shuffle=True):
        optimizer = tf.train.AdamOptimizer(learning_rate=0.001)
        train_op = optimizer.minimize(self.loss)
        losses = []
        for i in xrange(n_epochs):
            for batch_x, batch_y in self._iterate_minibatches(x, y, batch_size, shuffle):
                loss = sess.run([train_op, self.loss], feed_dict={self.inp: batch_x,
                                                                  self.out: batch_y})
                losses.append(loss)
        return np.array(losses).mean()





