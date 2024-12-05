import unittest
import Server.Path as P
import Server.Location as L
import math

def make_birdie(distance, degree):
        return L.BirdieLocation(distance * math.cos(math.radians(degree)), distance * math.sin(math.radians(degree)), 0, 0, True)


class TestPathPlanning(unittest.TestCase):
    def setUp(self):
        self.robot = L.RobotLocation(0, 0, 0, 0)
        self.radius = self.robot.center_to_grabber_tip
        self.birdie45 = make_birdie(self.radius * 2, 45)
        self.birdie70 = make_birdie(self.radius * 2, 70)
        self.birdie225 = make_birdie(self.radius * 2, 225)
        self.straight = L.Position(
            self.robot.x + 2 * self.radius * math.cos(self.robot.angle),
            self.robot.y +  2 * self.radius * math.sin(self.robot.angle),
            self.robot.z
            )

        self.robot45 = L.RobotLocation(0,0,0,math.radians(45))
        self.robot_pos_angle = L.RobotLocation(2,5,0,math.radians(137))

    def testOneBirdie(self):
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, [self.birdie45])
        self.assertEqual(next_birdie, self.birdie45)
        self.assertAlmostEqual(next_angle, math.radians(45))

    def testTwoBirdiesNoBlock(self):
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, [self.birdie45, L.BirdieLocation(-self.radius + 10, self.radius - 30, 0, 0, True)])
        self.assertEqual(next_birdie, self.birdie45)
        self.assertAlmostEqual(next_angle, math.radians(45))

    def testTwoBirdiesBlockLeftSide(self):
        block = make_birdie(self.radius, 30)
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, [self.birdie70, block])
        self.assertEqual(next_birdie, self.birdie70)
        self.assertAlmostEqual(next_angle, math.radians(70-360))

    def testTwoBirdiesBlockRightSide(self):
        block = make_birdie(self.radius, -30)
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, [self.birdie225, block])
        self.assertEqual(next_birdie, self.birdie225)
        self.assertAlmostEqual(next_angle, math.radians(225))

    def testMultipleNoTooClose(self):
        birdies = [make_birdie(self.radius * 4, 225), self.birdie45, make_birdie(3*self.radius, 30), make_birdie(4 * self.radius, 0)]
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, birdies)
        self.assertEqual(next_birdie, self.birdie45)
        self.assertAlmostEqual(next_angle, math.radians(45))

    def testMultipleNoBlock(self):
        birdies = [self.birdie45, L.BirdieLocation(0, self.radius - 10, 0, 0, True), L.BirdieLocation(-self.radius + 10, 0, 0, 0, True)]
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, birdies)
        self.assertEqual(next_birdie, self.birdie45)
        self.assertAlmostEqual(next_angle, math.radians(45))

    def testMultipleAllBlock(self):
        birdies = [make_birdie(self.radius, -30), make_birdie(self.radius, 70), make_birdie(self.radius, 30), self.birdie45]
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, birdies)
        self.assertEqual(next_birdie, self.straight)
        self.assertAlmostEqual(next_angle, 0)

    # The blocking birdie on the left has a wider angle but because of the angle of the grabber,
    # it would still be pushed away so we choose to go straight
    def testBlockBecuaseGripperAngle(self):
        birdies = [make_birdie(self.radius, 55), make_birdie(self.radius - 10, -50), self.birdie45]
        (next_birdie, next_angle) = P.next_collection_taget(self.robot, birdies)
        self.assertEqual(next_birdie, self.straight)
        self.assertAlmostEqual(next_angle, 0)

    def testAngles(self):
        (next_birdie, next_angle) = P.next_collection_taget(self.robot45, [self.birdie45])
        self.assertEqual(next_birdie, self.birdie45)
        self.assertAlmostEqual(next_angle, 0)

    def testAngles2(self):
        (next_birdie, next_angle) = P.next_collection_taget(self.robot45, [self.birdie70])
        self.assertEqual(next_birdie, self.birdie70)
        self.assertAlmostEqual(next_angle, math.radians(70) - self.robot45.angle)

    def testPosAndAngle(self):
        birdie = L.BirdieLocation(60 + self.robot_pos_angle.x, 60 + self.robot_pos_angle.y, 0, 0, True)
        (next_birdie, next_angle) = P.next_collection_taget(self.robot_pos_angle, [birdie])
        self.assertEqual(next_birdie, birdie)
        self.assertAlmostEqual(next_angle, math.radians(45) - self.robot_pos_angle.angle)

if __name__ == '__main__':
    unittest.main()