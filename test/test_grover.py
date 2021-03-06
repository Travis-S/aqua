# -*- coding: utf-8 -*-

# Copyright 2018 IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

import unittest
import itertools

from parameterized import parameterized
from qiskit.qobj import RunConfig

from qiskit.aqua import QuantumInstance, get_aer_backend
from qiskit.aqua.algorithms import Grover
from qiskit.aqua.components.oracles import LogicExpressionOracle
from test.common import QiskitAquaTestCase

grover_tests = [
    ['test_grover.cnf', False, 3],
    ['test_grover_tiny.cnf', False, 1],
    ['test_grover_no_solution.cnf', True, 1]
]
mct_modes = ['basic', 'advanced', 'noancilla']
simulators = ['qasm_simulator', 'statevector_simulator']
optimizations = ['off', 'espresso']


class TestGrover(QiskitAquaTestCase):
    @parameterized.expand(
        [x[0] + list(x[1:]) for x in list(itertools.product(grover_tests, mct_modes, simulators, optimizations))]
    )
    def test_grover(self, dimacs_file, incremental, num_iterations, mct_mode, simulator, optimization='off'):
        dimacs_file = self._get_resource_path(dimacs_file)
        # get ground-truth
        with open(dimacs_file) as f:
            buf = f.read()
        if incremental:
            self.log.debug('Testing incremental Grover search on SAT problem instance: \n{}'.format(
                buf,
            ))
        else:
            self.log.debug('Testing Grover search with {} iteration(s) on SAT problem instance: \n{}'.format(
                num_iterations, buf,
            ))
        header = buf.split('\n')[0]
        self.assertGreaterEqual(header.find('solution'), 0, 'Ground-truth info missing.')
        self.groundtruth = [
            ''.join([
                '1' if i > 0 else '0'
                for i in sorted([int(v) for v in s.strip().split() if v != '0'], key=abs)
            ])[::-1]
            for s in header.split('solutions:' if header.find('solutions:') >= 0 else 'solution:')[-1].split(',')
        ]
        backend = get_aer_backend(simulator)
        oracle = LogicExpressionOracle(buf, optimization=optimization)
        grover = Grover(
            oracle, num_iterations=num_iterations, incremental=incremental, mct_mode=mct_mode
        )
        run_config = RunConfig(shots=1000, max_credits=10, memory=False)
        quantum_instance = QuantumInstance(backend, run_config)

        ret = grover.run(quantum_instance)

        self.log.debug('Ground-truth Solutions: {}.'.format(self.groundtruth))
        self.log.debug('Top measurement:        {}.'.format(ret['top_measurement']))
        if ret['oracle_evaluation']:
            self.assertIn(ret['top_measurement'], self.groundtruth)
            self.log.debug('Search Result:          {}.'.format(ret['result']))
        else:
            self.assertEqual(self.groundtruth, [''])
            self.log.debug('Nothing found.')


if __name__ == '__main__':
    unittest.main()
