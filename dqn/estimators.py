
import tensorflow as tf
import os


class QvalueEstimatorBase(object):
    """
    Base class for any estimators: value, Q-value, policy, advantage etc.
    """
    def __init__(self,
                 inp_shape=None,
                 n_actions=None,
                 scope='estimator',
                 sum_dir=None):
        self.inp_shape = inp_shape
        self.n_actions = n_actions
        self.scope = scope
        self.summary_writer = None
        with tf.variable_scope(self.scope):
            self._build_model()
            if sum_dir:
                summary_folder = os.path.join(sum_dir, 'summary_{}'.format(scope))
                if not os.path.exists(sum_dir):
                    os.makedirs(sum_dir)
                self.summary_writer = tf.train.SummaryWriter(summary_folder)

    def _build_model(self):
        self.state_ph = tf.placeholder(shape=(None,) + self.inp_shape, dtype=tf.float32, name='x')
        self.target_ph = tf.placeholder(shape=(None,), dtype=tf.float32, name='y')
        self.actions_ph = tf.placeholder(shape=(None,), dtype=tf.int32, name='actions')
        self.q_all = self._build_network()
        self.actions_one_hot = tf.one_hot(self.actions_ph, self.n_actions, dtype=tf.float32)
        self.q = tf.reduce_sum(tf.matmul(self.actions_one_hot, self.q_all), reduction_indices=[1])
        self.losses = tf.squared_difference(self.q, self.target_ph)
        self.loss = tf.reduce_mean(self.losses)
        self.optimizer = tf.train.AdamOptimizer(learning_rate=0.001, beta1=0.9, beta2=0.999)
        self.train_op = self.optimizer.minimize(self.loss, global_step=tf.contrib.framework.get_global_step())
        self.summaries = tf.merge_summary([
            tf.scalar_summary('loss', self.loss),
            tf.histogram_summary('loss_histogram', self.losses),
            tf.histogram_summary('q_values_histogram', self.q_all),
            tf.scalar_summary('max_q_value', tf.reduce_max(self.q_all))
        ])

    def predict_q_values(self, sess, states):
        return sess.run(self.q_all, feed_dict={self.state_ph: states})

    def update_step(self, sess, states, targets, actions):
        feed_dict = {self.state_ph: states, self.target_ph: targets, self.actions_ph: actions}
        summaries, global_step, loss, _ = sess.run([self.summaries, tf.conrib.framework.get_global_step(),
                                                    self.loss, self.train_op], feed_dict=feed_dict)
        if self.summary_writer:
            self.summary_writer.add_summary(summaries, global_step)
        return loss

    def copy_parameters(self, sess, model_1, model_2):
        model_1_params = [t for t in tf.trainable_variables() if t.name.startswith(model_1.scope)]
        model_1_params = sorted(model_1_params, key=lambda v: v.name)
        model_2_params = [t for t in tf.trainable_variables() if t.name.startswith(model_2.scope)]
        model_2_params = sorted(model_2_params, key=lambda v: v.name)
        update_ops = []
        for p1, p2 in zip(model_1_params, model_2_params):
            op = p2.assign(p1)
            update_ops.append(op)
        sess.run(update_ops)

    def _build_network(self):
        raise NotImplementedError


class QvalueEstimatorConv(QvalueEstimator):
    """
    Convolutional neural network for Atari games.
    """
    def __init__(self, *args, **kwargs):
        super(QvalueEstimatorConv, self).__init__(*args, **kwargs)

    def _build_model_approximator(self):
        conv1 = tf.contrib.layers.conv2d(inputs=self.state_ph, num_outputs=32, kernel_size=(8, 8), stride=(4, 4),
                                         padding='SAME', activation_fn=tf.nn.relu)
        conv2 = tf.contrib.layers.conv2d(inputs=conv1, num_outputs=64, kernel_size=(4, 4), stride=(2, 2),
                                         padding='SAME', activation_fn=tf.nn.relu)
        conv3 = tf.contrib.layers.conv2d(inputs=conv2, num_outputs=64, kernel_size=(3, 3), stride=(1, 1),
                                         padding='SAME', activation_fn=tf.nn.relu)
        flattened = tf.contrib.layers.flatten(conv3)
        fc1 = tf.contrib.layers.fully_connected(flattened, 512)
        out = tf.contrib.layers.fully_connected(fc1, self.n_actions)
        return out


class QvalueEstimatorDense(QvalueEstimatorBase):
    """
    Convolutional neural network for Atari games.
    """

    def __init__(self, *args, **kwargs):
        super(QvalueEstimatorDense, self).__init__(*args, **kwargs)

    def _build_model_approximator(self):
        fc1 = tf.contrib.layers.fully_connected(self.state_ph, 128)
        fc2 = tf.contrib.layers.fully_connected(fc1, 32)
        out = tf.contrib.layers.fully_connected(fc2, self.n_actions)
        return out



def deep_q_learning(sess,
                    env,
                    q_model,
                    target_model,
                    state_processor,
                    num_episodes,
                    experiments_folder,
                    replay_memory_size,
                    replay_memory_size_init,
                    upd_target_freq=10000,
                    gamma=0.99,
                    eps_start=1.0,
                    eps_end=0.1,
                    eps_decay_steps=500000,
                    batch_size=128,
                    record_video_freq=50):



